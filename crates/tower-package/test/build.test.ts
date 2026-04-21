import { test } from "node:test";
import assert from "node:assert/strict";
import { gunzipSync } from "node:zlib";

import {
  buildBundle,
  type BundleInputs,
} from "../pkg/tower_package.js";

const enc = new TextEncoder();
const dec = new TextDecoder();

interface TarEntry {
  name: string;
  data: Uint8Array;
}

// Minimal ustar reader — enough to pull entry names and bodies out of the
// output. Not robust to long names, extensions, or PAX headers, which the
// builder never emits.
function parseTarEntries(data: Uint8Array): TarEntry[] {
  const entries: TarEntry[] = [];
  let offset = 0;
  while (offset + 512 <= data.length) {
    const header = data.subarray(offset, offset + 512);
    if (header.every((b) => b === 0)) break;

    const name = dec.decode(header.subarray(0, 100)).replace(/\0.*$/, "");
    if (!name) break;

    const sizeOctal = dec
      .decode(header.subarray(124, 136))
      .replace(/\0.*$/, "")
      .trim();
    const size = parseInt(sizeOctal, 8);

    const body = data.subarray(offset + 512, offset + 512 + size);
    entries.push({ name, data: body });

    offset += 512 + Math.ceil(size / 512) * 512;
  }
  return entries;
}

function minimalInputs(): BundleInputs {
  return {
    appFiles: [
      { archiveName: "app/main.py", bytes: enc.encode('print("hi")\n') },
      { archiveName: "app/helper.py", bytes: enc.encode("# helper\n") },
    ],
    moduleFiles: [],
    towerfileBytes: enc.encode('[app]\nname = "test"\n'),
    invoke: "main.py",
    parameters: [],
    importPaths: [],
  };
}

test("returns a gzipped archive", () => {
  const out = buildBundle(minimalInputs());
  assert.ok(out instanceof Uint8Array);
  assert.equal(out[0], 0x1f);
  assert.equal(out[1], 0x8b);
});

test("output is byte-deterministic across calls", () => {
  const a = buildBundle(minimalInputs());
  const b = buildBundle(minimalInputs());
  assert.deepEqual(a, b);
});

test("entries are sorted by archive name with MANIFEST and Towerfile last", () => {
  const entries = parseTarEntries(gunzipSync(buildBundle(minimalInputs())));
  assert.deepEqual(
    entries.map((e) => e.name),
    ["app/helper.py", "app/main.py", "MANIFEST", "Towerfile"],
  );
});

test("file contents round-trip through the archive", () => {
  const entries = parseTarEntries(gunzipSync(buildBundle(minimalInputs())));
  const main = entries.find((e) => e.name === "app/main.py")!;
  assert.equal(dec.decode(main.data), 'print("hi")\n');
});

test("manifest matches the inputs", () => {
  const entries = parseTarEntries(gunzipSync(buildBundle(minimalInputs())));
  const manifest = JSON.parse(
    dec.decode(entries.find((e) => e.name === "MANIFEST")!.data),
  );
  assert.equal(manifest.version, 3);
  assert.equal(manifest.invoke, "main.py");
  assert.equal(manifest.app_dir_name, "app");
  assert.equal(manifest.modules_dir_name, "modules");
  assert.equal(typeof manifest.checksum, "string");
  assert.equal(manifest.checksum.length, 64);
});

test("module files and import paths flow through", () => {
  const inputs = minimalInputs();
  inputs.moduleFiles = [
    {
      archiveName: "modules/shared/__init__.py",
      bytes: enc.encode(""),
    },
    {
      archiveName: "modules/shared/util.py",
      bytes: enc.encode("# util\n"),
    },
  ];
  inputs.importPaths = ["modules/shared"];

  const entries = parseTarEntries(gunzipSync(buildBundle(inputs)));
  const names = entries.map((e) => e.name);
  assert.ok(names.includes("modules/shared/__init__.py"));
  assert.ok(names.includes("modules/shared/util.py"));

  const manifest = JSON.parse(
    dec.decode(entries.find((e) => e.name === "MANIFEST")!.data),
  );
  assert.deepEqual(manifest.import_paths, ["modules/shared"]);
});

test("different inputs produce different checksums", () => {
  const a = parseTarEntries(gunzipSync(buildBundle(minimalInputs())));

  const other = minimalInputs();
  other.appFiles[0] = {
    archiveName: "app/main.py",
    bytes: enc.encode('print("bye")\n'),
  };
  const b = parseTarEntries(gunzipSync(buildBundle(other)));

  const checksumA = JSON.parse(
    dec.decode(a.find((e) => e.name === "MANIFEST")!.data),
  ).checksum;
  const checksumB = JSON.parse(
    dec.decode(b.find((e) => e.name === "MANIFEST")!.data),
  ).checksum;
  assert.notEqual(checksumA, checksumB);
});

test("invalid input shape throws", () => {
  assert.throws(() => buildBundle({} as unknown as BundleInputs));
});
