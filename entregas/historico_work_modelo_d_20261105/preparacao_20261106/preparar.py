"""Inventário dos dados recebidos; não reconstrói ticks nem executa o EA."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import openpyxl


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def prepare(data, out):
    adjustments = read_csv(data / "Ajustes_Diarios_Modelo_D_20230301_20260921.csv")
    operations = read_csv(data / "Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv")
    daily = read_csv(data / "Referencia_D_diário.csv")
    dates = {r["Data"] for r in daily}
    if len(dates) != len(daily) or {r["DataOperacional"] for r in adjustments} != dates:
        raise ValueError("Datas diárias e ajustes incompatíveis")
    if len(adjustments) != len(dates):
        raise ValueError("Ajustes duplicados")
    counts = Counter(r["Data"] for r in operations)
    sources = {}
    hashes = {}
    for filename, sheet in sorted({(r["ArquivoFonte"], r["AbaFonte"]) for r in adjustments}):
        path = data / "Fontes_Originais_Ajuste" / filename
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        by_date = defaultdict(list)
        for row in workbook[sheet].iter_rows(min_row=2, values_only=True):
            if isinstance(row[0], datetime):
                by_date[row[0].date().isoformat()].append(row[0])
        workbook.close()
        sources[filename, sheet] = by_date
    records = []
    for adj in sorted(adjustments, key=lambda r: r["DataOperacional"]):
        date = adj["DataOperacional"]
        cutoff = "17:45:00" if "2023-03-13" <= date <= "2023-11-03" else "18:00:00"
        if adj["ZeragemComparacaoWork"] != cutoff or int(adj["OperacoesD"]) != counts[date]:
            raise ValueError(f"Referência inconsistente em {date}")
        times = sorted(sources[adj["ArquivoFonte"], adj["AbaFonte"]].get(date, []))
        deltas = Counter(int((b - a).total_seconds()) for a, b in zip(times, times[1:]))
        records.append({
            "Data": date, "AjusteWork": adj["Ajuste"], "OperacoesWork": counts[date],
            "GranularidadeWork": "M5" if date < "2026-03-01" else "M1",
            "CorteWork": cutoff, "ArquivoFonteAjuste": adj["ArquivoFonte"],
            "AbaFonteAjuste": adj["AbaFonte"], "LinhasOHLCNaFonteAjuste": len(times),
            "PrimeiroHorarioFonte": times[0].strftime("%H:%M:%S") if times else "",
            "UltimoHorarioFonte": times[-1].strftime("%H:%M:%S") if times else "",
            "PassosObservadosSegundos": json.dumps(dict(sorted(deltas.items()))),
            "ContratoReal": adj["ContratoReal"], "DataFontePublicacao": adj["DataFontePublicacao"],
            "AjusteAnterior": adj["AjusteAnterior"],
            "CandlesOriginaisWorkConferidos": "NAO", "TicksReaisConferidos": "NAO",
            "EstadoBacktestEA": "PENDENTE_DADOS_E_ADAPTADOR",
        })
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "INVENTARIO_877_PREGOES.csv", records[0].keys(), records)
    pilot = [r for r in records if "2026-09-14" <= r["Data"] <= "2026-09-18"]
    write_csv(out / "PILOTO_20260914_20260918.csv", records[0].keys(), pilot)
    selected = [r for r in operations if "2026-09-14" <= r["Data"] <= "2026-09-18"]
    write_csv(out / "REFERENCIA_PILOTO_D.csv", operations[0].keys(), selected)
    # Nenhuma linha é marcada como processada: ainda não recebemos uma nova execução.
    write_csv(out / "COBERTURA_NOVA_EXECUCAO_MODELO.csv", ["Data", "Estado"], [])
    write_csv(out / "OPERACOES_NOVA_EXECUCAO_MODELO.csv", operations[0].keys(), [])
    summary = {
        "pregoes": len(records), "operacoes_referencia": len(operations),
        "pregoes_sem_operacao": sum(r["OperacoesWork"] == 0 for r in records),
        "contratos_reais_identificados": sum(bool(r["ContratoReal"]) for r in records),
        "backtests_ea_executados": 0,
        "piloto": {"inicio": "2026-09-14", "fim": "2026-09-18", "pregoes": len(pilot),
                   "operacoes_work": len(selected),
                   "pontos_work_por_contrato": str(sum((Decimal(r["Pontos"].replace(",", ".")) for r in selected), Decimal(0))),
                   "volume_planejado_ea_por_nivel": 5,
                   "criterio_selecao": "Semana civil completa recente dentro da amostra M1; sem otimização de resultados."},
        "hashes_fontes_ajuste": hashes,
        "limite": "Inventário de fontes de ajuste. Quantidade e horários não certificam a cobertura dos candles do Work nem de ticks reais.",
    }
    (out / "RESUMO_PREPARACAO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.dados, args.saida), ensure_ascii=False, indent=2))
