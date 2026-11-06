"""Verificações sintéticas da matemática e agregação; não são backtest."""
import unittest
from datetime import datetime, timedelta
from decimal import Decimal as D

from conferir import context, prices


class ContextTests(unittest.TestCase):
    def test_known_symmetric_levels_and_targets(self):
        pivot, r200, s200, entries, targets = prices(D(1000), D(1100), D(900), D(1000), D(1000))
        self.assertEqual((pivot, r200, s200), (D(1000), D(1200), D(800)))
        self.assertEqual(entries, {"S38.2": D("923.6"), "S50": D(900), "S61.8": D("876.4"),
                                   "R38.2": D("1076.4"), "R61.8": D("1123.6")})
        self.assertEqual(targets, {"S38.2": D("938.2"), "S50": D("923.6"), "S61.8": D(900),
                                   "R38.2": D("1047.2"), "R61.8": D("1111.8")})

    def test_aggregation_uses_chronological_open_close(self):
        start = datetime(2026, 9, 1, 9)
        bars = {start+timedelta(minutes=15*i): (D(100+i), D(150+i), D(90-i), D(110+i), D(123)) for i in reversed(range(38))}
        day = context(bars)["2026-09-01"]
        self.assertEqual((day["open"], day["high"], day["low"], day["close"]), (100, 187, 53, 147))
        self.assertTrue(day["cadence"])
        del bars[start+timedelta(minutes=15)]
        self.assertFalse(context(bars)["2026-09-01"]["cadence"])


if __name__ == "__main__":
    unittest.main()
