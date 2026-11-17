# SECURITY TODO — deferred hardening for the executable / trainer-UI phase

> Status: **intentionally deferred.** For the current shape of this app — a
> **local, single-user, non-auth** metadata viewer/editor — the items below are
> low practical risk. They become *important* the moment any of these is true:
> the server binds to a non-loopback interface, it gets exposed on a LAN/the
> internet, it becomes auth-facing, or it's embedded into the **trainer UI /
> full ecosystem** port. Revisit this file at that point.

## Context

The filesystem routes (`/api/fs`, `/api/image`, `/api/metadata`,
`/api/metadata-write`) accept a client-supplied `baseFolder` + `path` and read
(and, for `metadata-write`, write) files under it. This is **by design** — the
app is a local file browser that operates on whatever folder the user selects,
so there is no fixed server-side root to pin to.

`app/api/metadata-write/route.ts` is the only **write** route and is already
hardened against path traversal:
- containment via `path.relative` (no `startsWith` prefix-match bypass),
- `fs.realpath` symlink re-check on both base and target,
- PNG-only + "must be an existing file" gates, so its entire write capability is
  limited to "rewrite an existing PNG" or "create `<name>_edited.png` beside one".

## What's been done

### 1. CSRF / DNS-rebinding guard on `/api/metadata-write` (GET + POST) ✅
An `originGuard` function validates `Host` (loopback only) and `Origin` (must be
loopback if present) on every request to the write route. Kills both CSRF-style
blind writes and DNS-rebinding escalation without blocking local browsing.

### 2. Project-root containment ✅
`resolveTarget` now checks that `baseFolder` sits within `process.cwd()` before
allowing any path resolution, so a client-supplied baseFolder can't reach outside
the repo. The final write target (including `saveAsCopy` sibling names) is also
re-validated through the same containment pipeline.

### 3. Read routes folded onto the hardened helper ✅
`/api/fs`, `/api/image`, `/api/metadata` (GET) and `/api/thumbnail` all use the
shared `originGuard` + `resolveContained` helpers from `lib/fs-guard.ts`:
loopback-only host/origin gate plus `path.relative` containment (the old
`startsWith` prefix checks — vulnerable to sibling-folder tricks — are gone).
On any public deployment (Vercel demo) these routes refuse every request with
403 by design; the demo parses in-browser. Regression fixtures:
`scripts/generate-civitai-fixtures.mjs` → `fixtures/` (Civitai on-site params +
ComfyUI URN:AIR paths).

### 4. Loopback binding enforced in every launch path ✅
A `Host` header is client-controlled, so the `originGuard` host check is
defense-in-depth only — the binding is the real control. All three launch
paths now bind loopback: `next dev -H 127.0.0.1` (both the `dev` script and
`electron:dev`'s concurrently call), Electron's packaged-server spawn
(`HOSTNAME: '127.0.0.1'`, electron/main.ts), and the standalone pin
(`scripts/copy-standalone-assets.mjs` rewrites the server.js default from
`0.0.0.0` to `127.0.0.1` on every build).

## Still deferred

1. **`HOSTNAME` env override on the standalone server.** A caller can still set
   `HOSTNAME=0.0.0.0` for `npm start`; that's a deliberate operator action, not
   a default. If belt-and-braces is ever wanted, the postbuild script could
   refuse a non-loopback `HOSTNAME` explicitly.
2. **(Trainer-UI / ecosystem phase only)** If the embedded copy ever serves over
   a real interface or behind auth: add a per-session allowed-roots allowlist
   enforced server-side instead of trusting client `baseFolder`, plus standard
   CSRF tokens. That's the point where the "enterprise" treatment is warranted.
3. Residual accepted risk: another **local** process (same user account) can
   still reach these loopback endpoints, as it could reach any local app.
   Closing that fully would mean per-instance capabilities in Electron IPC.

## Pointers
- Shared guard helpers: `lib/fs-guard.ts` (`originGuard` / `resolveContained` /
  `isInside`) — mirrors the in-route copies that remain in
  `app/api/metadata-write/route.ts`, `app/api/safetensors/route.ts`, and
  `app/api/watch/route.ts` (hardened identically; consolidation into the shared
  helper is optional cleanup).
- Write route specifics: `app/api/metadata-write/route.ts`
  (`resolveTarget` / `isInside`).
