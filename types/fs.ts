export interface FsItem {
  name: string;
  isDirectory: boolean;
  path: string;
  size?: number;      // File size in bytes
  mtime?: number;     // Modified time in ms since epoch
  /**
   * Browser-picked (local mode) items carry the actual File object so bytes
   * can be parsed in-memory — no server-side path exists for these.
   */
  localFile?: File;
}
