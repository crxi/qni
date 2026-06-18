/**
 * Prepend Astro's BASE_URL to an internal path so links and static-asset
 * references resolve correctly regardless of the base the site is served
 * from. The site is now served from the root ("/") on Cloudflare Pages, so
 * this normalises leading slashes and is otherwise a passthrough — kept so
 * call sites stay correct if a subpath base is ever reintroduced.
 *
 *   url("/qubits")            → "/qubits"
 *   url("/icons/foo.svg")     → "/icons/foo.svg"
 *   url("/")                  → "/"
 */
export function url(path: string): string {
  const rawBase = import.meta.env.BASE_URL; // "/" — root base on Cloudflare Pages
  const base = rawBase.endsWith("/") ? rawBase : rawBase + "/";
  const cleaned = path.replace(/^\/+/, "");
  return cleaned ? base + cleaned : base;
}
