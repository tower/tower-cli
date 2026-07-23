use std::io::Read;
use std::rc::Rc;

use deno_core::error::ModuleLoaderError;
use deno_error::JsErrorBox;
use deno_core::{
    extension, op2, v8, FsModuleLoader, JsRuntime, ModuleLoadResponse, ModuleLoader, ModuleSource,
    ModuleSourceCode, ModuleSpecifier, ModuleType, PollEventLoopOptions, RequestedModuleType,
    ResolutionKind, RuntimeOptions, ToJsBuffer,
};
use serde::{Deserialize, Serialize};

const NODE_MODULES: &str = "/Users/bradhe/Development/tower/tower/tower-app2/node_modules";

/// The egress allowlist: the ONLY host the sandboxed engine may reach over the
/// network. Extension side-modules are served from bundled local files (see the
/// op), so the CDN is NOT reachable — only the catalog's S3.
const ALLOWED_HOSTS: &[&str] = &["127.0.0.1:9100"];

fn host_allowed(url: &deno_core::url::Url) -> bool {
    let host = url.host_str().unwrap_or("");
    let hostport = format!(
        "{host}{}",
        url.port().map(|p| format!(":{p}")).unwrap_or_default()
    );
    ALLOWED_HOSTS.contains(&host) || ALLOWED_HOSTS.contains(&hostport.as_str())
}

#[derive(Deserialize)]
struct HttpReq {
    method: String,
    url: String,
    headers: Vec<(String, String)>,
}

#[derive(Serialize)]
struct HttpResp {
    status: u16,
    headers: Vec<(String, String)>,
    body: ToJsBuffer,
}

/// Synchronous HTTP for the wasm engine's blocking XHR, gated by the allowlist.
/// Sync (not async) because DuckDB-wasm's blocking build issues synchronous
/// XMLHttpRequests; `ureq` is a blocking client with no tokio nesting.
#[op2]
#[serde]
fn op_http_sync(#[serde] req: HttpReq) -> Result<HttpResp, JsErrorBox> {
    let parsed =
        deno_core::url::Url::parse(&req.url).map_err(|e| JsErrorBox::generic(e.to_string()))?;

    // Serve DuckDB extension side-modules from bundled local files instead of
    // the CDN. This is the packaging requirement AND the big cold-start win —
    // it removes the internet round-trips that dominate startup. (Production
    // would embed these via include_bytes! rather than read from disk.)
    if parsed.host_str() == Some("extensions.duckdb.org") {
        let fname = parsed.path().rsplit('/').next().unwrap_or_default();
        let local = format!("assets/ext/{fname}");
        let bytes =
            std::fs::read(&local).map_err(|e| JsErrorBox::generic(format!("bundled ext {local}: {e}")))?;
        return Ok(HttpResp {
            status: 200,
            headers: vec![
                ("content-length".to_string(), bytes.len().to_string()),
                ("content-type".to_string(), "application/wasm".to_string()),
            ],
            body: bytes.into(),
        });
    }

    if !host_allowed(&parsed) {
        return Err(JsErrorBox::generic(format!("egress denied: {}", req.url)));
    }

    let mut r = ureq::request(&req.method, &req.url);
    for (k, v) in &req.headers {
        r = r.set(k, v);
    }
    let resp = match r.call() {
        Ok(resp) => resp,
        // Keep the HTTP response for non-2xx (404/416/…) — DuckDB reads the status.
        Err(ureq::Error::Status(_, resp)) => resp,
        Err(ureq::Error::Transport(t)) => return Err(JsErrorBox::generic(t.to_string())),
    };
    let status = resp.status();
    let headers = resp
        .headers_names()
        .into_iter()
        .filter_map(|name| resp.header(&name).map(|v| (name.clone(), v.to_string())))
        .collect();
    let mut body = Vec::new();
    resp.into_reader()
        .read_to_end(&mut body)
        .map_err(|e| JsErrorBox::generic(e.to_string()))?;
    Ok(HttpResp {
        status,
        headers,
        body: body.into(),
    })
}

extension!(tower_sandbox, ops = [op_http_sync]);

/// Wraps [`FsModuleLoader`], resolving bare specifiers (the duckdb-wasm glue
/// imports `apache-arrow`, which in turn pulls `tslib` etc.) via `node_modules`
/// by reading each package's ESM entry. Relative/absolute imports fall through
/// to the filesystem loader.
struct NodeModulesLoader {
    fs: FsModuleLoader,
}

fn resolve_bare(specifier: &str) -> Option<ModuleSpecifier> {
    let pkg_dir = format!("{NODE_MODULES}/{specifier}");
    let manifest = std::fs::read_to_string(format!("{pkg_dir}/package.json")).ok()?;
    let json: serde_json::Value = serde_json::from_str(&manifest).ok()?;
    let entry = json
        .get("module")
        .or_else(|| json.get("main"))
        .and_then(|v| v.as_str())
        .unwrap_or("index.js");
    ModuleSpecifier::from_file_path(format!("{pkg_dir}/{entry}")).ok()
}

impl ModuleLoader for NodeModulesLoader {
    fn resolve(
        &self,
        specifier: &str,
        referrer: &str,
        kind: ResolutionKind,
    ) -> Result<ModuleSpecifier, ModuleLoaderError> {
        // The glue's only external import is `apache-arrow`, used solely by the
        // Table-returning `query()` path. We drive `runQuery` (raw Arrow IPC
        // bytes) instead, so stub arrow out entirely and prune its whole subtree
        // (tslib, node:stream, ...).
        if specifier == "apache-arrow" {
            return Ok(ModuleSpecifier::parse("stub:apache-arrow").unwrap());
        }
        let bare = !specifier.starts_with('.')
            && !specifier.starts_with('/')
            && !specifier.starts_with("file:");
        if bare {
            if let Some(spec) = resolve_bare(specifier) {
                return Ok(spec);
            }
        }
        self.fs.resolve(specifier, referrer, kind)
    }

    fn load(
        &self,
        module_specifier: &ModuleSpecifier,
        maybe_referrer: Option<&ModuleSpecifier>,
        is_dyn_import: bool,
        requested_module_type: RequestedModuleType,
    ) -> ModuleLoadResponse {
        if module_specifier.scheme() == "stub" {
            let src = ModuleSource::new(
                ModuleType::JavaScript,
                ModuleSourceCode::String("export default {};".to_string().into()),
                module_specifier,
                None,
            );
            return ModuleLoadResponse::Sync(Ok(src));
        }
        self.fs
            .load(module_specifier, maybe_referrer, is_dyn_import, requested_module_type)
    }
}

const TABLE: &str = "iceberg_scan('s3://warehouse/bench')";

/// (label, sql, expected_scalar). Count is metadata-bound; the scan aggregation
/// forces reading the data columns from parquet on S3, which stresses the engine.
fn queries() -> Vec<(&'static str, String, i64)> {
    vec![
        (
            "count (metadata)",
            format!("SELECT count(*) AS n FROM {TABLE}"),
            1_000_000,
        ),
        (
            "scan+agg (id sum)",
            format!("SELECT sum(id)::BIGINT AS s FROM {TABLE}"),
            // sum(0..999999) = 499999500000
            499_999_500_000,
        ),
    ]
}

fn stats(times: &[std::time::Duration]) -> (f64, f64, f64) {
    let mut ms: Vec<f64> = times.iter().map(|d| d.as_secs_f64() * 1000.0).collect();
    ms.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let min = ms[0];
    let median = ms[ms.len() / 2];
    let mean = ms.iter().sum::<f64>() / ms.len() as f64;
    (min, median, mean)
}

/// Decode a single-cell Arrow IPC (the count) so we can confirm correctness.
fn decode_scalar(ipc: &[u8]) -> i64 {
    use arrow::array::Array;
    let reader = arrow::ipc::reader::FileReader::try_new(std::io::Cursor::new(ipc), None)
        .expect("arrow ipc file");
    for batch in reader {
        let batch = batch.unwrap();
        let col = batch.column(0);
        if let Some(a) = col.as_any().downcast_ref::<arrow::array::Int64Array>() {
            return a.value(0);
        }
        if let Some(a) = col.as_any().downcast_ref::<arrow::array::Decimal128Array>() {
            return a.value(0) as i64;
        }
    }
    -1
}

/// Native arm: the current tower-cli path — native DuckDB attaching S3 directly.
/// Returns per-query (warm times, scalar result), in the same order as queries().
fn native_bench(iters: usize) -> Vec<(Vec<std::time::Duration>, i64)> {
    let conn = duckdb::Connection::open_in_memory().unwrap();
    for s in ["INSTALL httpfs", "LOAD httpfs", "INSTALL iceberg", "LOAD iceberg"] {
        conn.execute_batch(s).unwrap();
    }
    conn.execute_batch(
        "CREATE SECRET s3sec (TYPE s3, KEY_ID 'minioadmin', SECRET 'minioadmin', \
         ENDPOINT '127.0.0.1:9100', URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')",
    )
    .unwrap();
    queries()
        .into_iter()
        .map(|(_, sql, _)| {
            let scalar: i64 = conn.query_row(&sql, [], |r| r.get(0)).unwrap(); // warmup
            let mut times = Vec::with_capacity(iters);
            for _ in 0..iters {
                let t = std::time::Instant::now();
                let _: i64 = conn.query_row(&sql, [], |r| r.get(0)).unwrap();
                times.push(t.elapsed());
            }
            (times, scalar)
        })
        .collect()
}

fn main() {
    let iters = 20;
    let t_read = std::time::Instant::now();
    let wasm = std::fs::read("assets/duckdb-eh.wasm").expect("read wasm");
    let read_ms = t_read.elapsed().as_secs_f64() * 1000.0;
    let bootstrap = include_str!("../assets/bootstrap.js");

    let tokio = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();

    // ---- WASM arm (deno_core sandbox) ----
    let cold = std::time::Instant::now();
    let (wasm_cold, wasm_warm) = tokio.block_on(async move {
        let loader = NodeModulesLoader { fs: FsModuleLoader };
        let mut rt = JsRuntime::new(RuntimeOptions {
            module_loader: Some(Rc::new(loader)),
            extensions: vec![tower_sandbox::init_ops()],
            ..Default::default()
        });
        {
            let scope = &mut rt.handle_scope();
            let store = v8::ArrayBuffer::new_backing_store_from_vec(wasm).make_shared();
            let ab = v8::ArrayBuffer::with_backing_store(scope, &store);
            let global = scope.get_current_context().global(scope);
            let key = v8::String::new(scope, "__DUCKDB_WASM__").unwrap();
            global.set(scope, key.into(), ab.into());
        }
        rt.execute_script("bootstrap.js", bootstrap).expect("bootstrap");
        let init_ms = cold.elapsed().as_secs_f64() * 1000.0; // runtime + bootstrap

        let path = std::env::current_dir().unwrap().join("assets/driver.mjs");
        let specifier = deno_core::ModuleSpecifier::from_file_path(&path).unwrap();
        let t_load = std::time::Instant::now();
        let mod_id = rt.load_main_es_module(&specifier).await.expect("load");
        let glue_compile_ms = t_load.elapsed().as_secs_f64() * 1000.0; // compile 1.1MB glue
        let eval = rt.mod_evaluate(mod_id);
        rt.run_event_loop(PollEventLoopOptions::default())
            .await
            .expect("event loop");
        eval.await.expect("eval");
        // cold = instantiate + extension load + first (warmup) S3 query
        let cold = cold.elapsed();
        {
            let scope = &mut rt.handle_scope();
            let global = scope.get_current_context().global(scope);
            let out_k = v8::String::new(scope, "__out").unwrap();
            let out = global.get(scope, out_k.into()).unwrap().to_rust_string_lossy(scope);
            assert_eq!(out, "ready", "wasm driver setup failed: {out}");
            let tk = v8::String::new(scope, "__timings").unwrap();
            let timings = global.get(scope, tk.into()).unwrap().to_rust_string_lossy(scope);
            println!("=== COLD START BREAKDOWN (ms) ===");
            println!("  wasm file read (34MB from disk): {read_ms:.0}");
            println!("  V8 runtime + bootstrap:          {init_ms:.0}");
            println!("  compile glue JS (1.1MB):         {glue_compile_ms:.0}");
            println!("  JS phases: {timings}");
            println!("  TOTAL cold: {:.0}\n", cold.as_secs_f64() * 1000.0);
        }

        // For each query: warm loop of synchronous __runSql(sql) calls, then
        // decode the last IPC result to confirm the scalar.
        let mut per_query = Vec::new();
        for (_, sql, _) in queries() {
            let call = format!("globalThis.__runSql({sql:?})");
            let _ = rt.execute_script("warm.js", call.clone()).expect("warmup"); // warm this query
            let mut warm = Vec::with_capacity(iters);
            for _ in 0..iters {
                let t = std::time::Instant::now();
                rt.execute_script("q.js", call.clone()).expect("q");
                warm.push(t.elapsed());
            }
            let scope = &mut rt.handle_scope();
            let global = scope.get_current_context().global(scope);
            let key = v8::String::new(scope, "__lastIpc").unwrap();
            let val = global.get(scope, key.into()).unwrap();
            let arr = v8::Local::<v8::Uint8Array>::try_from(val).unwrap();
            let mut buf = vec![0u8; arr.byte_length()];
            arr.copy_contents(&mut buf);
            per_query.push((warm, decode_scalar(&buf)));
        }
        (cold, per_query)
    });

    // ---- Native arm (current tower-cli path) ----
    let native = native_bench(iters);

    println!("\n=== native (current) vs wasm-sandbox — iceberg over MinIO, 1M rows, {iters} warm iters ===");
    println!(
        "wasm cold start (instantiate 34MB + load extensions + first query): {:.0} ms\n",
        wasm_cold.as_secs_f64() * 1000.0
    );
    println!(
        "{:<20} {:>10} {:>22} {:>22} {:>10}",
        "query", "expected", "native median (ms)", "wasm median (ms)", "wasm/native"
    );
    for (i, (label, _, expected)) in queries().into_iter().enumerate() {
        let (nt_times, nt_val) = &native[i];
        let (wm_times, wm_val) = &wasm_warm[i];
        let (_, nt_med, _) = stats(nt_times);
        let (_, wm_med, _) = stats(wm_times);
        let ok = *nt_val == expected && *wm_val == expected;
        println!(
            "{:<20} {:>10} {:>22.2} {:>22.2} {:>9.1}x  {}",
            label,
            expected,
            nt_med,
            wm_med,
            wm_med / nt_med,
            if ok { "OK" } else { "MISMATCH" }
        );
    }
}
