import {useEffect,useSyncExternalStore} from 'react';
import {subscribeMarket,getMarketSnapshot,applyMarketSnapshot,markMarketOffline} from './market-data.js';
import {startMarketPolling} from './market-poller.js';
export function useMarketData({marketUrl='/api/market',requireHeartbeat=false}={}){
 const snapshot=useSyncExternalStore(subscribeMarket,getMarketSnapshot);
 useEffect(()=>startMarketPolling({url:marketUrl,onData:data=>applyMarketSnapshot(data,{requireHeartbeat}),onFailure:markMarketOffline}),[marketUrl,requireHeartbeat]);
 return snapshot;
}
