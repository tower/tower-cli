import * as duckdb from './duckdb-browser-blocking.mjs';

// Instantiate the engine and open a connection against the MinIO-backed Iceberg
// table, then expose a warm-query closure the Rust host calls in a timed loop.
// All network goes through the sync XHR shim -> allowlisted host op.
globalThis.__out = null;
globalThis.__q = null;
globalThis.__lastIpc = null;
(async () => {
  try {
    const T = [];
    const mark = (l) => T.push([l, Date.now()]);
    mark('start');
    const bundles = {
      eh: { mainModule: 'duckdb-eh.wasm', mainWorker: null, pthreadWorker: null },
    };
    const db = await duckdb.createDuckDB(bundles, new duckdb.ConsoleLogger(), duckdb.BROWSER_RUNTIME);
    mark('createDuckDB');
    await db.instantiate(() => {});
    mark('instantiate wasm');
    db.open({});
    const conn = db.connect();
    const run = (sql) => conn.useUnsafe((b, cid) => b.runQuery(cid, sql));
    mark('open+connect');

    run('LOAD httpfs');
    mark('LOAD httpfs (CDN)');
    run('LOAD iceberg');
    mark('LOAD iceberg (CDN)');
    run(
      "CREATE SECRET s3sec (TYPE s3, KEY_ID 'minioadmin', SECRET 'minioadmin', " +
        "ENDPOINT '127.0.0.1:9100', URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')",
    );
    mark('create secret');

    globalThis.__runSql = (sql) => {
      const ipc = run(sql);
      globalThis.__lastIpc = ipc; // Uint8Array; Rust reads + decodes for correctness
      return ipc.length;
    };
    // warm the first S3 metadata read out of the timed loop
    globalThis.__runSql("SELECT count(*) FROM iceberg_scan('s3://warehouse/bench')");
    mark('first S3 query');
    const deltas = [];
    for (let i = 1; i < T.length; i++) deltas.push([T[i][0], T[i][1] - T[i - 1][1]]);
    globalThis.__timings = JSON.stringify(deltas);
    globalThis.__out = 'ready';
  } catch (e) {
    globalThis.__out = 'ERROR: ' + (e && e.stack ? e.stack : String(e));
  }
})();
