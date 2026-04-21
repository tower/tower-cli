export interface PackageEntry {
  archiveName: string;
  bytes: Uint8Array;
}

export interface PackageParameter {
  name: string;
  description?: string;
  default: string;
  hidden: boolean;
}

export interface PackageInputs {
  appFiles: PackageEntry[];
  moduleFiles: PackageEntry[];
  towerfileBytes: Uint8Array;
  invoke: string;
  parameters: PackageParameter[];
  importPaths: string[];
}

/**
 * Build a Tower app package (gzipped tar) from in-memory file contents.
 *
 * Output is byte-identical across runs for the same inputs: entries are
 * sorted by archiveName, tar headers are normalized (zero mtime/uid/gid,
 * mode 0644), and the gzip header embeds no mtime.
 */
export function buildPackage(inputs: PackageInputs): Uint8Array;
