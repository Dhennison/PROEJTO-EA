"""Compara a amostra exportada de 09:00 de WINZ26 com a barra M1.

Análise offline de dados fornecidos; não reproduz API/validação do MT5.
Uso: python3 CONFERIR_AMOSTRA_TICKS_M1.py > COMPARACAO_TICKS_M1.json
Arquivos originais ficam ao lado do script; nenhuma entrada é modificada.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_rows(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


ticks = read_rows("WINZ26_202610300900_202610300901.csv")
bars = read_rows("WINZ26_M1_202610300900_202610301824.csv")
begin = datetime(2026, 10, 30, 9)
end = datetime(2026, 10, 30, 9, 1)
times = [datetime.strptime(r["<DATE>"] + " " + r["<TIME>"],
                           "%Y.%m.%d %H:%M:%S.%f") for r in ticks]
minute = [r for r, timestamp in zip(ticks, times) if begin <= timestamp < end]
# As colunas de cotação no export são esparsas. Não converter Bid/Ask em Last
# nem preencher células de Last vazias com valores de registros anteriores.
trade = [r for r in minute if int(r["<FLAGS>"]) & (8 | 16 | 32 | 64)
         and r["<LAST>"] and Decimal(r["<LAST>"]) > 0]
if not trade:
    raise SystemExit("Sem negócios Last positivos na amostra selecionada")
prices = [Decimal(r["<LAST>"]) for r in trade]
observed = {"OPEN": prices[0], "HIGH": max(prices), "LOW": min(prices),
            "CLOSE": prices[-1],
            "VOL": sum((Decimal(r["<VOLUME>"]) for r in trade
                        if r["<VOLUME>"]), Decimal(0))}
bar = next(r for r in bars if r["<DATE>"] == "2026.10.30"
           and r["<TIME>"] == "09:00:00")
comparison = {k: {"from_trades": str(v), "M1": bar[f"<{k}>"],
                  "equal": v == Decimal(bar[f"<{k}>"])}
              for k, v in observed.items()}
result = {
    "scope": "Amostra atual do terminal; não prova conteúdo do agente no ensaio",
    "interval": "[2026-10-30 09:00:00, 2026-10-30 09:01:00)",
    "export_rows": len(ticks), "rows_in_minute": len(minute),
    "rows_outside_minute": len(ticks) - len(minute),
    "positive_last_trade_rows": len(trade),
    "first_trade_time": trade[0]["<TIME>"],
    "last_trade_time": trade[-1]["<TIME>"],
    "timestamp_regressions": sum(a > b for a, b in zip(times, times[1:])),
    "flags_in_minute": dict(Counter(r["<FLAGS>"] for r in minute)),
    "zero_flags_rows": [r for r in minute if int(r["<FLAGS>"]) == 0],
    "M1_tick_volume": bar["<TICKVOL>"], "comparison": comparison,
    "all_compared_values_equal": all(v["equal"] for v in comparison.values()),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
