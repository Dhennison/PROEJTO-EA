"""Fixtures sintéticas: verificam o comparador, não a execução do Modelo D."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comparar_teorico import compare


def operation(day="2026-09-14"):
    return {"Data": day, "Nível": "S50", "Lado": "COMPRA", "Abertura": "101000",
            "Linha": "100000", "Entrada": "100000", "Stop": "99625", "Alvo": "100200",
            "Hora entrada": "10:00:00", "Hora saída": "11:00:00", "Saída": "100200",
            "Motivo": "ALVO", "Pontos": "200", "Ambíguo": "", "Zeragem": "18:00:00"}


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.dates = ["2026-09-14", "2026-09-15"]
        self.coverage = [{"Data": d, "Estado": "PROCESSADO"} for d in self.dates]

    def test_no_data_is_not_missing_trade(self):
        report, diffs, days, _ = compare([operation()], [], self.dates, [])
        self.assertEqual(report["estado"], "SEM_NOVA_EXECUCAO")
        self.assertEqual(diffs, [])
        self.assertEqual(days, [])
        self.assertFalse(report["dd_periodo_integral_certificado"])

    def test_processed_zero_detects_missing_and_keeps_zero_day(self):
        report, diffs, days, _ = compare([operation()], [], self.dates, self.coverage)
        self.assertEqual(report["estado"], "COMPLETO")
        self.assertEqual(diffs[0]["Estado"], "AUSENTE_NOVA_ROTINA")
        self.assertEqual(len(days), 2)
        self.assertEqual(days[1]["PontosWork"], "0")

    def test_extra_on_reference_zero_day(self):
        _, diffs, _, _ = compare([], [operation(self.dates[1])], self.dates, self.coverage)
        self.assertEqual(diffs[0]["Estado"], "EXTRA_NOVA_ROTINA")

    def test_partial_excludes_unprocessed_dates(self):
        summary, diffs, _, _ = compare([operation(self.dates[1])], [], self.dates, self.coverage[:1])
        self.assertEqual(summary["estado"], "PARCIAL")
        self.assertEqual(summary["pregoes_pendentes"], [self.dates[1]])
        self.assertEqual(diffs, [])

    def test_price_and_reason_changes_are_reported(self):
        changed = operation() | {"Stop": "99630", "Motivo": "STOP", "Pontos": "-370"}
        _, diffs, _, _ = compare([operation()], [changed], self.dates, self.coverage)
        self.assertEqual(diffs[0]["Estado"], "DIVERGENTE")
        self.assertEqual(set(diffs[0]["CamposDiferentes"].split(", ")), {"Stop", "Motivo", "Pontos"})

    def test_rejects_duplicate_and_uncovered_operations(self):
        with self.assertRaises(ValueError):
            compare([], [operation(), operation()], self.dates, self.coverage)
        with self.assertRaises(ValueError):
            compare([], [operation()], self.dates, [])

    def test_rejects_invalid_numbers_and_wrong_side(self):
        for update in ({"Pontos": "NaN"}, {"Lado": "VENDA"}, {"Data": "2026-09-31"}):
            with self.assertRaises(ValueError):
                compare([], [operation() | update], self.dates, self.coverage)

    def test_decimal_display_noise_and_daily_dd(self):
        unchanged = operation() | {"Entrada": "100000.00000000001"}
        report, diffs, _, _ = compare([operation()], [unchanged], self.dates, self.coverage)
        self.assertEqual(diffs[0]["Estado"], "COMPATIVEL")
        loss = operation(self.dates[1]) | {"Pontos": "-375", "Motivo": "STOP"}
        report, _, _, totals = compare([operation(), loss], [unchanged, loss], self.dates, self.coverage)
        self.assertEqual(report["dd_nova_sequencia_datas_processadas"], "375")
        self.assertEqual(next(r for r in totals if r["Periodo"] == "TOTAL")["PontosWork"], "-175")


if __name__ == "__main__":
    unittest.main()
