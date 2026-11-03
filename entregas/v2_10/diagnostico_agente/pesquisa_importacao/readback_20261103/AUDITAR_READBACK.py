"""Compara o CSV original com a exportacao nativa do simbolo de pesquisa.

Somente le os CSVs; grava resultados JSON/TXT. Nao altera dados de mercado.
Contagens de negocio sao derivadas de flags/Last no CSV, nao de uma API MT5.
"""
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "DADOS_ORIGINAIS/WINZ26_202610300900_202610300901.csv"
READBACK = ROOT / "MD_PESQ_WINZ26_1030_READBACK.csv"
HEADER = ["<DATE>", "<TIME>", "<BID>", "<ASK>", "<LAST>", "<VOLUME>", "<FLAGS>"]


def number(value):
    result = Decimal(value or "0")
    if not result.is_finite():
        raise ValueError("Non-finite CSV number")
    return result


def load(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows or rows[0] != HEADER or any(len(row) != 7 for row in rows):
        raise ValueError("Unexpected header or field count: " + path.name)
    for row in rows[1:]:
        datetime.strptime(row[0] + " " + row[1], "%Y.%m.%d %H:%M:%S.%f")
        for value in row[2:]:
            number(value)
        int(row[6])
    return rows[1:]


def metadata(path):
    data = path.read_bytes()
    return {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "crlf": data.count(b"\r\n")}


def stats(rows):
    minute = [row for row in rows if row[0] == "2026.10.30" and "09:00:00.000" <= row[1] < "09:01:00.000"]
    trades = [row for row in minute if int(row[6]) & 120 and number(row[4]) > 0]
    prices = [number(row[4]) for row in trades]
    stamps = [(row[0], row[1]) for row in rows]
    return {
        "rows": len(rows), "minute_rows": len(minute),
        "boundary_rows": sum(row[:2] == ["2026.10.30", "09:01:00.000"] for row in rows),
        "timestamp_regressions": sum(a > b for a, b in zip(stamps, stamps[1:])),
        "flag_counts": dict(sorted(Counter(int(row[6]) for row in rows).items())),
        "explicit_all_zero_csv_lines": [index + 2 for index, row in enumerate(rows)
                                         if all(value != "" and number(value) == 0 for value in row[2:])],
        "minute_positive_trade_rows_from_csv_flags": len(trades),
        "minute_trade_volume_from_csv": str(sum((number(row[5]) for row in trades), Decimal(0))),
        "minute_trade_ohlc_from_csv": ([str(prices[0]), str(max(prices)), str(min(prices)), str(prices[-1])]
                                       if prices else None),
    }


def main():
    original, readback = load(ORIGINAL), load(READBACK)
    differences = []
    for index, (a, b) in enumerate(zip(original, readback)):
        if a != b:
            differences.append({"csv_line": index + 2, "original": dict(zip(HEADER, a)),
                                "readback": dict(zip(HEADER, b)),
                                "changed_columns": [name for name, x, y in zip(HEADER, a, b) if x != y]})
    same_count = len(original) == len(readback)
    same_stamps = same_count and all(a[:2] == b[:2] for a, b in zip(original, readback))
    result = {
        "original": {**metadata(ORIGINAL), **stats(original)},
        "readback": {**metadata(READBACK), **stats(readback)},
        "byte_identical": ORIGINAL.read_bytes() == READBACK.read_bytes(),
        "same_row_count": same_count, "same_dates_times_and_order": same_stamps,
        "unchanged_paired_rows": min(len(original), len(readback)) - len(differences),
        "changed_paired_rows": len(differences),
        "changed_column_counts": dict(Counter(name for diff in differences for name in diff["changed_columns"])),
        "differences": differences,
        "scope": "CSV comparison only; no claim of internal MT5 cause, native API result or Tester success",
    }
    (ROOT / "COMPARACAO.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "COMPARACAO INTEGRAL DO READBACK — 03/11/2026",
        "CSV original e CSV de saida preservados; nenhum registro foi editado/removido.",
        f"Registros: original={len(original)}; readback={len(readback)}.",
        f"Identicos byte a byte: {result['byte_identical']}.",
        f"Mesmos pares data/hora e ordem: {same_stamps}.",
        f"Linhas pareadas identicas: {result['unchanged_paired_rows']}; alteradas: {len(differences)}.",
        "",
    ]
    for tag in ("original", "readback"):
        item = result[tag]
        lines.extend([
            f"{tag}: bytes={item['bytes']}; SHA256={item['sha256']}",
            f"Minuto09:00: linhas={item['minute_rows']}; negocios positivos segundo flags/Last do CSV="
            f"{item['minute_positive_trade_rows_from_csv_flags']}; volume somado={item['minute_trade_volume_from_csv']}",
            f"OHLC de negocios no minuto={item['minute_trade_ohlc_from_csv']}",
            f"Linhas totalmente zeradas={item['explicit_all_zero_csv_lines']}; registros no limite09:01={item['boundary_rows']}",
            "",
        ])
    for item in differences:
        a, b = item["original"], item["readback"]
        lines.extend([
            f"Linha CSV {item['csv_line']}, {a['<DATE>']} {a['<TIME>']}",
            "  original BID/ASK/LAST/VOLUME/FLAGS=" + "/".join(a[name] for name in HEADER[2:]),
            "  readback BID/ASK/LAST/VOLUME/FLAGS=" + "/".join(b[name] for name in HEADER[2:]),
        ])
    lines.extend([
        "", "INTERPRETACAO",
        "Os sete registros explicitamente zerados no original saem com precos, volume e flags26/28/30 no readback.",
        "A amostra exportada nao e copia fiel: tem sete eventos adicionais classificados como negocio pelos flags.",
        "O volume somado de negocios no minuto sobe14, de78471 para78485; OHLC permanece igual.",
        "Demais21563 linhas, inclusive vazios, sao identicas; quatro eventos do limite preservados.",
        "A comparacao observa o percurso importar/armazenar/exportar; nao identifica sua causa interna exata.",
        "Nao alegar que a consulta CopyTicksRange do agente ja foi executada ou retornara essas contagens.",
        "", "PROXIMO CONTROLE",
        "Prosseguir somente como diagnostico de ingestao no simbolo custom com essa diferenca conhecida.",
        "Nao editar CSV nem excluir zeros para forcar equivalencia. Preservar original e readback.",
        "Expert ja compilado Diagnostico_Importacao_WINZ26, simbolo MD_PESQ_WINZ26_1030, M5,",
        "30/10 a31/10/2026, cada tick baseado em ticks reais, sem visualizacao/otimizacao e agente local.",
        "Antes de iniciar, usuario envia captura das configuracoes. Prova em09:01; consulta somente09:00.",
        "Comparar consulta ALL/TRADE, flags, volume e M1 com os DOIS CSVs e inspecionar log do agente.",
        "Aceitacao desse controle nao certifica a amostra original nem o backtest do contrato negociavel.",
    ])
    (ROOT / "RESULTADO_COMPARACAO.txt").write_text("\n".join(lines) + "\n")
    print(json.dumps({key: result[key] for key in ("byte_identical", "same_row_count", "same_dates_times_and_order", "unchanged_paired_rows", "changed_paired_rows")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
