"""Cenários de calendário e seleção de fonte que não usam resultados do Work."""
import unittest

from replay_completo import cutoff_for, select_source

NAMES = ("WIN$N_M5_202302271510_202312281820.csv",
         "WINFUT_F_0_5min_01-01-2024_31-12-2024.csv",
         "WINFUT_F_0_5min_01-01-2025_31-12-2025.csv",
         "WINFUT_F_0_5min_01-01-2026_28-02-2026.csv",
         "WINFUT_F_0_1min_01-01-2026_22-09-2026.csv")


class TransitionTests(unittest.TestCase):
    def test_previous_day_uses_previous_year(self):
        self.assertEqual(select_source("2025-12-30", NAMES), NAMES[2])
        self.assertEqual(select_source("2026-01-02", NAMES), NAMES[3])

    def test_m1_overlap_does_not_replace_february_m5(self):
        self.assertEqual(select_source("2026-02-27", NAMES), NAMES[3])
        self.assertEqual(select_source("2026-03-02", NAMES), NAMES[4])

    def test_2023_inclusive_cutoff_boundaries(self):
        for day, expected in (("2023-03-10", "18:00:00"), ("2023-03-13", "17:45:00"),
                              ("2023-11-03", "17:45:00"), ("2023-11-06", "18:00:00"),
                              ("2024-03-13", "18:00:00")):
            self.assertEqual(cutoff_for(day), expected)


if __name__ == "__main__":
    unittest.main()
