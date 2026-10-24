// The standalone and HQ mount share the same visual assets without root-relative URLs.
export function assetUrl(base = '/', name) {
  return `${String(base).replace(/\/+$/, '')}/assets/${name}`;
}
