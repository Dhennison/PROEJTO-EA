import csv
import sys
import unittest
from pathlib import Path
from decimal import Decimal as D

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from analisar_focal import tick_stats,validate_ticks

def tick(index,ms,last,flags=56):
    return dict(indice=str(index),time=str(ms//1000),time_msc=str(ms),bid='100',ask='105',last=str(last),volume='1',volume_real='1',flags=str(flags))

class AnalysisTests(unittest.TestCase):
    def test_ohlc_filter_sequence_and_exclusive_end(self):
        rows=[tick(0,60000000,100),tick(1,60000000,110),tick(2,60000001,999,6),tick(3,60060000,200)]
        self.assertEqual(tick_stats(rows,60000000,60060000),dict(O=D(100),H=D(110),L=D(100),C=D(110)))

    def test_precision_preserved(self):
        r=[tick(0,60000000,'100.0000000001'),tick(1,60000001,'100.0000000002')]
        self.assertEqual(tick_stats(r,60000000,60060000)['H'],D('100.0000000002'))

    def test_invalid_csv_snapshots_rejected(self):
        for rows,count in [([tick(0,60060000,100)],1),([tick(2,60000000,100)],1),([tick(0,60000000,'NaN')],1),([tick(0,60000000,0)],1),([tick(0,60000000,100)],2)]:
            with self.assertRaises(ValueError):validate_ticks(rows,count,60000000,60060000)

    def test_milliseconds_same_time_keeps_source_order(self):
        rows=[tick(0,60000000,105),tick(1,60000000,100)]
        validate_ticks(rows,2,60000000,60060000)
        self.assertEqual(tick_stats(rows,60000000,60060000)['C'],D(100))

    def test_empty_is_not_zero_price(self):
        self.assertIsNone(tick_stats([],60000000,60060000))

    def test_no_order_transport_in_sources(self):
        import re
        for p in (ROOT/'MQL5').rglob('*'):
            if p.suffix in ('.mq5','.mqh'):
                self.assertFalse(re.search(r'\b(OrderSend|OrderSendAsync|OrderCheck|WebRequest)\s*\(',p.read_text()))

if __name__=='__main__':unittest.main()
