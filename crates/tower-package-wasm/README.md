# tower-package-wasm

WebAssembly bindings for building Tower app bundles from TypeScript.

Wraps `tower-package-core::build_package` via `wasm-bindgen` and produces
an npm-publishable package with TypeScript types.

## Build

From inside the nix devshell (`nix develop`):

```sh
./scripts/build.sh              # --target bundler (default, for webpack/vite/rollup)
./scripts/build.sh web          # --target web (native ES modules, fetch-based init)
./scripts/build.sh nodejs       # --target nodejs (CommonJS, Node 18+)
```

Output lands in `pkg/`.

## Usage

```ts
import { buildBundle, BundleInputs } from 'tower-package-wasm';

const inputs: BundleInputs = {
  appFiles: [
    { archiveName: 'app/main.py', bytes: new TextEncoder().encode('print("hi")') },
  ],
  moduleFiles: [],
  towerfileBytes: new TextEncoder().encode('[app]\nname = "my-app"\n'),
  invoke: 'main.py',
  parameters: [],
  importPaths: [],
};

const tarGz: Uint8Array = buildBundle(inputs);
```

Archive names must already be rooted under `app/` or `modules/<name>/`;
the core does no path rewriting.

Output is byte-deterministic for a given input: entries are sorted by
`archiveName`, tar headers are normalized (zero mtime/uid/gid, mode
`0644`), and the gzip header embeds no mtime. The bundle format
(`ustar` + gzip, `MANIFEST` + `Towerfile` at the top level) matches
what the Tower CLI produces.
