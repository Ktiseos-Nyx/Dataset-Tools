# Standalone Server Integrity (verify-before-spawn) — Plan

**Status:** Spec — not yet implemented
**Date:** 2026-10-04

---

## 1. Context & Problem

The packaged app is split in two, and only half of it is tamper-checked:

| Location | Contents | Protected? |
|---|---|---|
| `app.asar` | `.electron/main.js`, `preload.js`, `package.json` | ✅ via `enableEmbeddedAsarIntegrityValidation` + `onlyLoadAppFromAsar` |
| `resources/standalone/` | Next.js `server.js`, `node_modules/` (sharp + `@img/*.node`), `.next/` | ❌ no protection |

The fuses validate **`app.asar` only**. The standalone tree — which contains the *entire* actual application (metadata parser, every API route, sharp) — ships as a loose folder via `extraResources`, outside asar, with no integrity check. An attacker with write access to the install dir can swap `server.js`, a sharp binary, or any `.next` chunk and nothing detects it.

This is **CWE-353 — Missing Support for Integrity Check**: the packaged app executes the standalone server through `ELECTRON_RUN_AS_NODE` without verifying its contents first, and neither `enableEmbeddedAsarIntegrityValidation` nor `onlyLoadAppFromAsar` covers a server copied through `extraResources`.

## 2. Why the standalone can't live inside asar

1. **It's a separate process.** Spawned via `ELECTRON_RUN_AS_NODE=1 process.execPath server.js`; `child_process.spawn` needs a real on-disk path, not one inside a virtual asar filesystem.
2. **sharp's native addons.** `.node` binaries can't be `require`d from inside asar — they must be real files.

So the standalone *must* stay outside asar. The goal is to still detect tampering there.

## 3. Goal

Detect tampering of the shipped standalone tree before it executes, via a
**verify-before-spawn** check in the Electron main process (which itself lives
inside the integrity-protected `app.asar`, so the check is trustworthy).

## 4. Design

1. **Build time** (electron-builder `afterPack` hook, or extend the existing `scripts/copy-standalone-assets.mjs`): compute a hash of the `standalone/` tree and write the expected hash **into `app.asar`** (a small `standalone.sha256` file, or embed as a constant in compiled `main.js`). Because `app.asar` is integrity-validated, the stored hash can't be tampered with.
2. **Runtime** (`main.ts`, immediately before `startNextServer` spawns): verify the standalone tree. A naive "hash then spawn" has a **TOCTOU gap** — an attacker can modify files between the hash and the exec. So the bytes you verify must be the bytes you run: copy the `standalone/` tree to a private, write-protected snapshot, verify *that* snapshot, then spawn from it — or use an OS-enforced mechanism that authenticates files on read. Hashing the writable tree in place and then spawning it is not sufficient.

## 5. Open questions (decide before building)

1. **Hash scope** — whole-tree digest vs a manifest of per-file hashes. A manifest pinpoints *which* file changed and makes exclusions explicit.
2. **Exclusions** — is there any runtime-mutable state inside the standalone tree? Expected: no — `.thumbcache`/`.cache`/settings route to `userData` via `ELECTRON_USER_DATA`, so the packaged tree should be read-only and static. Confirm before relying on it.
3. **Cost** — SHA-256 over ~100–150 MB adds cold-start latency, and the TOCTOU-safe snapshot *also* means copying that tree to a private location every launch (doubling the I/O). Acceptable, or use BLAKE3 (far faster) / hash a strategic subset (server.js + `.next` + a node_modules manifest, skipping the large sharp binary)? Note sharp is itself a supply-chain target, so skipping it weakens coverage.
4. **Failure mode** — hard-fail (refuse to launch) vs warn-and-continue. Hard-fail is the point of integrity; on a read-only install dir, false positives should be near-zero.
5. **Where the hash lives** — a file read out of `app.asar` (simplest) vs embedded in `main.js`.

## 6. Alternatives (rejected)

- **Move standalone into asar + `asarUnpack`** — can't spawn a child process from asar, and native `.node` addons still can't load from inside it.
- **Authenticode code signing** — signs the EXE, not the loose standalone files; doesn't cover this gap.
- **`asarIntegrity` on `extraResources`** — that option only hashes asar archives, not a raw file tree.

## 7. Out of scope

- Code signing (separate posture decision).
- Auto-update integrity (no updater exists yet).
- Protecting runtime-mutable user data in `userData/` — that's the user's own data, not shipped code.

## 8. Rollout

| Phase | Deliverable |
|---|---|
| 0 | Answer the open questions (hash scope, cost, failure mode) |
| 1 | Build-time hash → embed in `app.asar` |
| 2 | Runtime verify-and-spawn in `main.ts` (TOCTOU-safe snapshot, or OS-enforced read-time auth) |
| 3 | Test: clean install, tampered `server.js`, tampered sharp binary, legitimate reinstall/update |
