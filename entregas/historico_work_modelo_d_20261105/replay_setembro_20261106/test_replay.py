"""Cenários sintéticos independentes da lista Work para regras intrabar/corte."""
import unittest
from datetime import datetime
from decimal import Decimal as D, localcontext

from replay import Bar, calculate, parse_bars, replay_day


def bar(hhmm, o, h, l, c, day="2026-09-01"):
    return Bar(datetime.fromisoformat(day+" "+hhmm+":00"), *(D(x) for x in (o, h, l, c)))


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.previous = [bar("09:00", 1000, 1100, 900, 1000, "2026-08-31")]
        self.first = bar("09:03", 1000, 1010, 950, 980)
        self.cut = bar("18:00", 850, 2000, 0, 1000)

    def run_day(self, sequence, adjustment=1000):
        with localcontext() as ctx:
            ctx.prec = 40
            return replay_day(sequence, self.previous, D(adjustment), "18:00:00")

    def test_stop_first_on_entry_bar(self):
        ops, _ = self.run_day([self.first, bar("10:00", 910, 950, 500, 900), self.cut])
        op = next(r for r in ops if r["Nível"] == "S50")
        self.assertEqual((op["Motivo"], op["Pontos"], op["Ambíguo"]), ("STOP", "-375.000000", "SIM"))
        self.assertEqual(op["Hora entrada"], op["Hora saída"])

    def test_cutoff_open_overrides_high_low(self):
        ops, _ = self.run_day([self.first, bar("10:00", 910, 915, 890, 900), self.cut])
        op = next(r for r in ops if r["Nível"] == "S50")
        self.assertEqual((op["Motivo"], op["Saída"], op["Pontos"]), ("ZERAGEM 18H", "850", "-50.000000"))

    def test_no_new_entry_on_cutoff_bar(self):
        ops, states = self.run_day([self.first, self.cut])
        self.assertFalse(any(r["Nível"] == "S50" for r in ops))
        self.assertEqual(next(r for r in states if r["Nivel"] == "S50")["Estado"], "SEM_TOQUE_ANTES_CORTE")

    def test_missing_cutoff_fails_instead_of_inventing_close(self):
        with self.assertRaises(ValueError):
            self.run_day([self.first])

    def test_equal_opening_is_valid_and_delayed_open_is_used(self):
        ops, _ = self.run_day([bar("09:03", 1000, 1001, 999, 1000), self.cut], adjustment=1200)
        op = next(r for r in ops if r["Nível"] == "S50")
        self.assertEqual((op["Entrada"], op["Hora entrada"]), ("1000.0", "09:03:00"))

    def test_prices_preserve_half_targets_and_support_stop_650(self):
        _, _, _, entries, targets = calculate(D(1000), D(1100), D(900), D(1000), D(1000))
        self.assertEqual(targets["R61.8"], D("1111.8"))
        self.assertEqual(targets["S38.2"], D("938.2"))
        self.assertEqual(entries["S61.8"]-D(650), D("226.4"))

    def test_profit_thousands_and_reverse_order(self):
        raw = "Ativo;Data;Hora;Abertura;Máximo;Mínimo;Fechamento;Volume;Quantidade\nWINFUT;01/09/2026;09:04:00;187.980;188.000;187.900;187.950;0;0\nWINFUT;01/09/2026;09:03:00;187.900;187.990;187.850;187.980;0;0\n".encode("cp1252")
        bars = parse_bars("WINFUT_M1.csv", raw)
        self.assertEqual((bars[0].stamp.minute, bars[0].o, bars[-1].c), (3, D(187900), D(187950)))
        with self.assertRaises(ValueError):
            parse_bars("WINFUT_M1.csv", raw+raw.splitlines(keepends=True)[1])


if __name__ == "__main__":
    unittest.main()
