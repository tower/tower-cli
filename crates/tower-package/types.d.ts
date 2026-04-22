export interface PackageEntry {
  archiveName: string;
  bytes: Uint8Array;
}

export interface PackageInputs {
  appFiles: PackageEntry[];
  moduleFiles: PackageEntry[];
  towerfileBytes: Uint8Array;
}

/**
 * Build a Tower app package (gzipped tar) from in-memory file contents.
 *
 * invoke, parameters, and import paths in the manifest are derived from
 * towerfileBytes, so the caller cannot produce a package whose manifest
 * disagrees with the embedded Towerfile.
 *
 * Output is byte-identical across runs for the same inputs: entries are
 * sorted by archiveName, tar headers are normalized (zero mtime/uid/gid,
 * mode 0644), and the gzip header embeds no mtime.
 */
export function buildPackage(inputs: PackageInputs): Uint8Array;
