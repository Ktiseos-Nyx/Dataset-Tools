/**
 * Launches the standalone server with a sanitized binding environment.
 *
 * Why this exists: the standalone server.js binds `process.env.HOSTNAME`
 * (falling back to the postbuild-pinned 127.0.0.1). HOSTNAME is an *ambient*
 * variable — shells (bash sets it to the machine name), CI runners, and other
 * software may have it set without the operator ever choosing anything — and
 * any non-loopback value makes the server listen on a reachable interface.
 *
 * So: neutralize ambient HOSTNAME, loopback by default, and reserve a
 * dedicated, explicitly-named variable (DT_HOSTNAME) for deliberate overrides.
 */
process.env.HOSTNAME = process.env.DT_HOSTNAME ?? '127.0.0.1';

await import('../.next/standalone/server.js');
