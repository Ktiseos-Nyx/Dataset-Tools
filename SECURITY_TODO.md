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
  limited to "rewrite an existing PNG" or "create `<name>.edited.png` beside one".

## What's still open (and why it's deferred, not ignored)

### 1. CSRF-style blind write on `POST /api/metadata-write`
`request.json()` parses the body regardless of `Content-Type`, so a malicious
web page you visit *while the app is running* can send a no-preflight
cross-origin POST (`Content-Type: text/plain`) and trigger a write. It's a
**blind** write — CORS blocks reading the response, so the attacker can't
enumerate the filesystem and must *guess* an exact path to an existing `.png`.
Worst case on a lucky guess: garbled metadata on one image (pixels untouched).
Low probability, low blast radius today.

### 2. DNS rebinding (the real escalation)
Rebinding can make a malicious domain resolve to `127.0.0.1`, becoming
*same-origin* with the app and defeating the "can't read responses" limit —
enabling enumeration via `/api/fs` then targeted writes. Mitigated by a `Host`
header check (below).

## Proportionate fixes to apply when porting / packaging

1. **Bind to `127.0.0.1` only — never `0.0.0.0`.** Single most important control
   for the packaged executable; keeps the server off the network entirely.
   (`next start -H 127.0.0.1`, or the equivalent in the Electron/embedded host.)
2. **`Origin` + `Host` guard on the write route (and ideally all fs routes).**
   ~5 lines: reject a `POST` whose `Origin` header is present and not the app's
   own origin, and reject any `Host` that isn't loopback. Kills both the CSRF
   POST and DNS rebinding cheaply, without touching the local-browsing design.
3. **(Trainer-UI / ecosystem phase only)** If the embedded copy ever serves over
   a real interface or behind auth: add a per-session allowed-roots allowlist
   enforced server-side instead of trusting client `baseFolder`, plus standard
   CSRF tokens. That's the point where the "enterprise" treatment is warranted.

## Pointers
- Write route: `app/api/metadata-write/route.ts` (`resolveTarget` / `isInside`)
- Shared-but-weaker read-route validation: `app/api/fs/route.ts`,
  `app/api/image/route.ts`, `app/api/metadata/route.ts` (still use the
  `startsWith` prefix check — fold them onto the hardened helper when convenient).
