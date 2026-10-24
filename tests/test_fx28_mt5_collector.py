from __future__ import annotations
import importlib.util
import io
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fx28_reader', ROOT/'backend/local-runner/hq_backend/research/fx_trend_mt5.py')
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


def symbol(name='EURUSD', **kwargs):
    return SimpleNamespace(**dict({'name':name,'currency_base':'EUR','currency_profit':'USD',
                                  'trade_calc_mode':0,'visible':False,'custom':False}, **kwargs))


class Fx28CollectorTests(unittest.TestCase):
    def test_exact_symbol_is_preferred_to_broker_suffix(self):
        self.assertEqual(reader.choose_symbol('EURUSD',[symbol('EURUSD.a'),symbol()]),('EURUSD',None))

    def test_symbol_mapping_uses_currencies_and_rejects_custom(self):
        self.assertEqual(reader.choose_symbol('EURUSD',[symbol('FAKE',custom=True)]),(None,'symbol_unavailable'))
        self.assertEqual(reader.choose_symbol('EURUSD',[symbol('EURUSD',currency_base='XAU')]),(None,'symbol_unavailable'))
        self.assertEqual(reader.choose_symbol('EURUSD',[symbol('EURUSD.a'),symbol('EURUSD.b')]),(None,'symbol_ambiguous'))

    def test_unique_visible_broker_suffix(self):
        self.assertEqual(reader.choose_symbol('EURUSD',[symbol('EURUSD.a'),symbol('EURUSD.b',visible=True)]),('EURUSD.b',None))

    def test_clock_requires_multiple_live_advancing_quotes(self):
        now=1792738275
        first={p:now+10800-3 for p in ('EURUSD','GBPUSD','USDJPY')}
        second={p:now+10800-1 for p in first}
        result=reader.verified_clock(first,second,now)
        self.assertEqual(result['offsetSeconds'],10800)
        self.assertEqual(result['method'],'live_tick_progress')
        with self.assertRaisesRegex(reader.DataUnavailable,'broker_clock_unverified'):
            reader.verified_clock(second,second,now)
        with self.assertRaises(reader.DataUnavailable):
            reader.verified_clock({'EURUSD':first['EURUSD']},{'EURUSD':second['EURUSD']},now)

    def test_clock_rejects_conflicting_or_nonfinite_quotes(self):
        now=1792738275
        with self.assertRaises(reader.DataUnavailable):
            reader.verified_clock({}, {'a':float('nan'),'b':float('inf'),'c':now+1,'d':now+3601},now)

    def test_verified_weekend_clock_hint_expires(self):
        now=datetime(2026,10,24,tzinfo=timezone.utc)
        hint={'offsetSeconds':10800,'verifiedAt':(now-timedelta(days=1)).isoformat()}
        self.assertEqual(reader.verified_clock({}, {}, now.timestamp(), hint)['method'],'previous_verified_live_ticks')
        hint['verifiedAt']=(now-timedelta(days=9)).isoformat()
        with self.assertRaises(reader.DataUnavailable): reader.verified_clock({}, {}, now.timestamp(), hint)
        hint={'offsetSeconds':True,'verifiedAt':now.isoformat()}
        with self.assertRaises(reader.DataUnavailable): reader.verified_clock({}, {}, now.timestamp(), hint)

    def fake_sdk(self):
        sdk=mock.Mock()
        sdk.initialize.return_value=True
        sdk.terminal_info.return_value=SimpleNamespace(path=str(ROOT/'fake-terminal'),data_path=str(ROOT/'fake-data'),connected=True)
        sdk.symbols_get.return_value=[symbol()]
        sdk.symbol_info_tick.return_value=SimpleNamespace(time=1792749075)
        sdk.copy_rates_from_pos.return_value=[dict(time=1792747800,open=1,high=2,low=.5,close=1.5,tick_volume=10,real_volume=0,spread=2)]
        for frame in reader.TIMEFRAMES: setattr(sdk,'TIMEFRAME_'+frame,frame)
        return sdk

    def test_clock_hint_rejects_naive_timestamp_and_future_normalized_quotes(self):
        now=datetime(2026,10,24,tzinfo=timezone.utc)
        hint={'offsetSeconds':7200,'verifiedAt':(now-timedelta(days=1)).isoformat()}
        stopped={pair:now.timestamp()+10800-1 for pair in ('EURUSD','GBPUSD','USDJPY')}
        with self.assertRaises(reader.DataUnavailable):
            reader.verified_clock(stopped,stopped,now.timestamp(),hint)
        hint['verifiedAt']='2026-10-23T00:00:00'
        with self.assertRaises(reader.DataUnavailable):
            reader.verified_clock({}, {}, now.timestamp(),hint)

    def test_collect_only_closed_bars_without_orders_or_account_reads(self):
        sdk=self.fake_sdk()
        clock={'offsetSeconds':10800,'verifiedAt':'2026-10-23T06:51:15Z','method':'live_tick_progress'}
        with mock.patch.object(reader,'verified_clock',return_value=clock):
            result=reader.collect(sdk,ROOT/'fake-terminal/terminal64.exe',ROOT/'fake-data','mtc-testfixture',lambda:None,pause=lambda _:None)
        self.assertEqual(len(result['pairs']),28)
        eur=next(p for p in result['pairs'] if p['pair']=='EURUSD')
        self.assertEqual(eur['series']['M15'][0]['time'],1792737000)
        self.assertEqual(eur['series']['M15'][0]['brokerTime'],1792747800)
        self.assertEqual(sdk.copy_rates_from_pos.call_count,5)
        for call in sdk.copy_rates_from_pos.call_args_list: self.assertEqual(call.args[2:],(1,200))
        self.assertFalse(sdk.account_info.called)
        self.assertFalse(sdk.order_send.called)
        self.assertFalse(sdk.positions_get.called)
        self.assertFalse(sdk.login.called)
        self.assertFalse(sdk.symbol_select.called)
        sdk.shutdown.assert_called_once()

    def test_changed_process_is_rejected_before_sdk_initialization(self):
        sdk=self.fake_sdk()
        with self.assertRaises(reader.DataUnavailable):
            reader.collect(sdk,ROOT/'fake-terminal/terminal64.exe',ROOT/'fake-data','mtc-testfixture',mock.Mock(side_effect=reader.DataUnavailable('changed')))
        sdk.initialize.assert_not_called()

    def test_binding_mismatch_disconnects_without_reading_prices(self):
        sdk=self.fake_sdk()
        sdk.terminal_info.return_value.data_path=str(ROOT/'other-terminal')
        with self.assertRaisesRegex(reader.DataUnavailable,'binding_mismatch'):
            reader.collect(sdk,ROOT/'fake-terminal/terminal64.exe',ROOT/'fake-data','mtc-testfixture',lambda:None)
        sdk.copy_rates_from_pos.assert_not_called()
        sdk.shutdown.assert_called_once()

    def test_dependency_hashes_cover_supported_python_versions(self):
        requirements=(ROOT/'requirements-runner.txt').read_text()
        self.assertIn('MetaTrader5==5.0.6231;',requirements)
        self.assertIn('numpy==2.2.6;',requirements)
        self.assertIn('numpy==2.3.5;',requirements)
        self.assertNotIn('--trusted-host',requirements)

    def test_main_transports_thai_metadata_with_windows_cp1252_stdout(self):
        expected={'schemaVersion':reader.SCHEMA,'source':{'timeNoteTh':'เวลาแท่งราคาจริง'},'pairs':[]}
        raw=io.BytesIO()
        stdout=io.TextIOWrapper(raw,encoding='cp1252')
        args=['reader','--terminal-path',str(ROOT/'terminal64.exe'),'--data-path',str(ROOT),
              '--candidate-id','mtc-testfixture','--terminal-pid','123']
        with mock.patch.object(reader.sys,'argv',args), mock.patch.object(reader.sys,'stdout',stdout), \
             mock.patch.dict(reader.sys.modules,{'MetaTrader5':mock.Mock()}), \
             mock.patch.object(reader,'process_guard',return_value=(lambda:None,lambda:None)), \
             mock.patch.object(reader,'collect',return_value=expected):
            code=reader.main()
        stdout.flush()
        self.assertEqual(code,0)
        self.assertEqual(json.loads(raw.getvalue().decode('ascii')),expected)


if __name__ == '__main__': unittest.main()
