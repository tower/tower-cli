export interface BundleEntry {
  archiveName: string;
  bytes: Uint8Array;
}

export interface BundleParameter {
  name: string;
  description?: string;
  default: string;
  hidden: boolean;
}

export interface BundleInputs {
  appFiles: BundleEntry[];
  moduleFiles: BundleEntry[];
  towerfileBytes: Uint8Array;
  invoke: string;
  parameters: BundleParameter[];
  schedule?: string;
  importPaths: string[];
}

/**
 * Build a Tower app bundle (gzipped tar) from in-memory file contents.
 *
 * Output is byte-identical across runs for the same inputs: entries are
 * sorted by archiveName, tar headers are normalized (zero mtime/uid/gid,
 * mode 0644), and the gzip header embeds no mtime.
 */
export function buildBundle(inputs: BundleInputs): Uint8Array;
