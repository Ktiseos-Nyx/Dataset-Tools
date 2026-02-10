export interface FsItem {
  name: string;
  isDirectory: boolean;
  path: string;
  size?: number;      // File size in bytes
  mtime?: number;     // Modified time in ms since epoch
}
