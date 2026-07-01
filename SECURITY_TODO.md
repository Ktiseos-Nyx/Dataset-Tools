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

## Still deferred

1. **Bind to `127.0.0.1` only — never `0.0.0.0`.** Single most important control
   for the packaged executable; keeps the server off the network entirely.
   (`next start -H 127.0.0.1`, or the equivalent in the Electron/embedded host.)
   Not yet done because `next dev` doesn't support `-H` the same way and the
   app is currently used only via `npm run dev`.
2. **(Trainer-UI / ecosystem phase only)** If the embedded copy ever serves over
   a real interface or behind auth: add a per-session allowed-roots allowlist
   enforced server-side instead of trusting client `baseFolder`, plus standard
   CSRF tokens. That's the point where the "enterprise" treatment is warranted.

## Pointers
- Write route: `app/api/metadata-write/route.ts` (`resolveTarget` / `isInside`)
- Shared-but-weaker read-route validation: `app/api/fs/route.ts`,
  `app/api/image/route.ts`, `app/api/metadata/route.ts` (still use the
  `startsWith` prefix check — fold them onto the hardened helper when convenient).
