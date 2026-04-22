# tower-package

Bundle builder for Tower apps. Used by the Tower CLI to pack an app
directory into a gzipped tar archive, and published as an npm package
(`tower-package-wasm`) for building bundles from TypeScript.

The crate has three layers:

- **Core** (always compiled) — pure types and the `build_package`
  function that turns in-memory bytes into a deterministic tar.gz.
- **Native** (`native` feature, default) — `Package::build` walks the
  filesystem, resolves globs, reads files, and delegates to the core.
  Used by the Tower CLI.
- **WASM** (`wasm` feature) — `wasm-bindgen` wrapper exposing
  `buildBundle` to JavaScript.

## Native (Rust)

```toml
[dependencies]
tower-package = "0.3"   # default features include `native`
```

Existing CLI callers are unchanged.

## WebAssembly (TypeScript)

Build from inside the nix devshell (`nix develop`):

```sh
./scripts/build.sh            # bundler (webpack/vite/rollup) — default
./scripts/build.sh web        # native ES modules, fetch-based init
./scripts/build.sh nodejs     # CommonJS, Node 18+
```

Output lands in `pkg/` and is publishable to npm as `tower-package-wasm`.

### Usage

```ts
import { buildPackage, PackageInputs } from 'tower-package-wasm';

const inputs: PackageInputs = {
  appFiles: [
    { archiveName: 'app/main.py', bytes: new TextEncoder().encode('print("hi")') },
  ],
  moduleFiles: [],
  towerfileBytes: new TextEncoder().encode(
    '[app]\nname = "my-app"\nscript = "main.py"\n',
  ),
};

const tarGz: Uint8Array = buildPackage(inputs);
```

Archive names must already be rooted under `app/` or `modules/<name>/`;
the core does no path rewriting. `invoke`, `parameters`, and import
paths in the manifest are derived from `towerfileBytes`.

Output is byte-deterministic for a given input: entries are sorted by
`archiveName`, tar headers are normalized (zero mtime/uid/gid, mode
`0644`), and the gzip header embeds no mtime. The package format
(`ustar` + gzip, `MANIFEST` + `Towerfile` at the top level) matches
what the Tower CLI produces natively.

## Tests

```sh
cargo test -p tower-package            # native Rust tests
./scripts/build.sh nodejs              # then
cd test && npm install && npm test     # TypeScript tests
```
