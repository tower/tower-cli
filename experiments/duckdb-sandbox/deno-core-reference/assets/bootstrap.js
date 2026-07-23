// Minimal browser-ish environment for the duckdb-wasm glue under bare deno_core.
// Everything the engine needs to reach the outside world funnels through `fetch`,
// which is the single egress-control point.
(() => {
  const g = globalThis;
  g.self = g;
  // Leave `window` undefined so the glue's `typeof window` guards take the
  // non-DOM path.
  g.navigator = g.navigator || { userAgent: 'tower-cli', hardwareConcurrency: 1 };

  // DuckDB's WASI random device needs crypto.getRandomValues. (Spike uses
  // Math.random; the real host would back this with an op over a CSPRNG.)
  g.crypto = g.crypto || {
    getRandomValues: (arr) => {
      for (let i = 0; i < arr.length; i++) arr[i] = (Math.random() * 256) | 0;
      return arr;
    },
  };
  g.performance = g.performance || { now: () => 0 };

  // Timers: the Emscripten runtime uses setTimeout/clearTimeout. Defer via
  // microtask (ignore the delay), with cancellation support.
  let __timerId = 1;
  const __timers = new Map();
  g.setTimeout = (fn, _ms, ...args) => {
    const id = __timerId++;
    __timers.set(id, true);
    Promise.resolve().then(() => {
      if (__timers.delete(id)) {
        try {
          fn(...args);
        } catch (e) {
          console.error(e);
        }
      }
    });
    return id;
  };
  g.clearTimeout = (id) => {
    __timers.delete(id);
  };
  g.setInterval = () => 0;
  g.clearInterval = () => {};
  g.queueMicrotask = g.queueMicrotask || ((fn) => Promise.resolve().then(fn));

  const print =
    g.Deno && g.Deno.core && g.Deno.core.print ? g.Deno.core.print : () => {};
  g.console = g.console || {
    log: (...a) => print(a.map(String).join(' ') + '\n'),
    error: (...a) => print('[err] ' + a.map(String).join(' ') + '\n'),
    warn: (...a) => print(a.map(String).join(' ') + '\n'),
    info: (...a) => print(a.map(String).join(' ') + '\n'),
    debug: () => {},
  };

  if (typeof g.TextEncoder === 'undefined') {
    g.TextEncoder = class TextEncoder {
      encode(str) {
        str = String(str);
        const bytes = [];
        for (let i = 0; i < str.length; i++) {
          let c = str.codePointAt(i);
          if (c > 0xffff) i++;
          if (c < 0x80) bytes.push(c);
          else if (c < 0x800) bytes.push(0xc0 | (c >> 6), 0x80 | (c & 0x3f));
          else if (c < 0x10000)
            bytes.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 0x3f), 0x80 | (c & 0x3f));
          else
            bytes.push(
              0xf0 | (c >> 18),
              0x80 | ((c >> 12) & 0x3f),
              0x80 | ((c >> 6) & 0x3f),
              0x80 | (c & 0x3f),
            );
        }
        return new Uint8Array(bytes);
      }
    };
  }
  if (typeof g.TextDecoder === 'undefined') {
    g.TextDecoder = class TextDecoder {
      decode(buf) {
        const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf.buffer || buf);
        let out = '';
        for (let i = 0; i < b.length; ) {
          let c = b[i++];
          if (c >= 0xf0) c = ((c & 0x07) << 18) | ((b[i++] & 0x3f) << 12) | ((b[i++] & 0x3f) << 6) | (b[i++] & 0x3f);
          else if (c >= 0xe0) c = ((c & 0x0f) << 12) | ((b[i++] & 0x3f) << 6) | (b[i++] & 0x3f);
          else if (c >= 0x80) c = ((c & 0x1f) << 6) | (b[i++] & 0x3f);
          out += String.fromCodePoint(c);
        }
        return out;
      }
    };
  }

  g.Request = g.Request || class Request {
    constructor(url, init) {
      this.url = String(url && url.url ? url.url : url);
      if (init) Object.assign(this, init);
    }
  };
  g.Response = g.Response || class Response {
    constructor(body, init) {
      this._body = body;
      this.ok = true;
      this.status = (init && init.status) || 200;
      this.headers = { get: () => 'application/wasm' };
    }
    arrayBuffer() {
      return Promise.resolve(this._body);
    }
    clone() {
      return this;
    }
  };

  // The Emscripten loader prefers streaming compile; make it work off our
  // buffer-backed Response instead of a real network stream.
  const WA = g.WebAssembly;
  WA.instantiateStreaming = async (src, imports) => {
    const resp = await src;
    return WA.instantiate(await resp.arrayBuffer(), imports);
  };
  WA.compileStreaming = async (src) => {
    const resp = await src;
    return WA.compile(await resp.arrayBuffer());
  };

  g.fetch = async (url) => {
    const u = String(url && url.url ? url.url : url);
    if (u.includes('.wasm')) {
      return new g.Response(g.__DUCKDB_WASM__, { status: 200 });
    }
    throw new Error('fetch blocked (not allowlisted): ' + u);
  };

  // The DuckDB-wasm *blocking* build does synchronous XHR for all HTTP/S3 I/O.
  // Back it with the sync host op, which enforces the egress allowlist.
  g.XMLHttpRequest = class XMLHttpRequest {
    constructor() {
      this._h = [];
      this._rh = [];
      this.status = 0;
      this.readyState = 0;
      this.response = null;
      this.responseText = '';
      this.responseType = '';
      this.DONE = 4;
    }
    open(method, url) {
      this._m = method;
      this._u = url;
      this.readyState = 1;
    }
    setRequestHeader(k, v) {
      this._h.push([k, String(v)]);
    }
    overrideMimeType() {}
    getResponseHeader(name) {
      const n = name.toLowerCase();
      const f = this._rh.find(([k]) => k.toLowerCase() === n);
      return f ? f[1] : null;
    }
    getAllResponseHeaders() {
      return this._rh.map(([k, v]) => k + ': ' + v).join('\r\n');
    }
    send() {
      let r;
      try {
        r = Deno.core.ops.op_http_sync({ method: this._m, url: this._u, headers: this._h });
      } catch (e) {
        this.status = 0;
        this.readyState = 4;
        if (this.onerror) this.onerror(e);
        return;
      }
      this.status = r.status;
      this._rh = r.headers;
      if (this.responseType === 'arraybuffer') this.response = r.body.buffer;
      else {
        this.responseText = new TextDecoder().decode(r.body);
        this.response = this.responseText;
      }
      this.readyState = 4;
      if (this.onreadystatechange) this.onreadystatechange();
      if (this.onload) this.onload();
    }
  };
})();
