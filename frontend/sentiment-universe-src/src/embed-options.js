export function normalizeEmbedOptions(options={}, origin) {
  const sameOrigin = value => {
    const url = new URL(value, origin);
    if (url.origin !== new URL(origin).origin || url.username || url.password) throw new Error('same_origin_required');
    return url;
  };
  const assetBase = sameOrigin(options.assetBase || '/frontend/public/sentiment-universe/');
  if (!assetBase.pathname.endsWith('/')) assetBase.pathname += '/';
  assetBase.search = ''; assetBase.hash = '';
  const marketUrl = sameOrigin(options.marketUrl || new URL('market.json', assetBase).href).href;
  const setup = new URL(options.setupUrl || 'http://127.0.0.1:4197/connect', origin);
  if (setup.protocol !== 'http:' || setup.hostname !== '127.0.0.1' || setup.username || setup.password || setup.pathname !== '/connect' || setup.search || setup.hash) throw new Error('local_setup_required');
  return {assetBase:assetBase.href,marketUrl,setupUrl:setup.href,embedded:true,requireHeartbeat:true};
}
