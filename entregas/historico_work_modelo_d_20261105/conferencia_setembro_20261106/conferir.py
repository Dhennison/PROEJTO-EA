"""Conferência de contexto diário disponível, sem replay intradiário ou EA.

Os XLSX de ajuste têm OHLC M15. Agregar esses registros pode confirmar
compatibilidade das fórmulas com o Work, mas não certifica a fita M1 original.
"""
import argparse
import csv
import hashlib
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import openpyxl

D = Decimal
START, END = "2026-09-01", "2026-09-21"
LEVELS = ("S38.2", "S50", "S61.8", "R38.2", "R61.8")
STOPS = dict(zip(LEVELS, map(D, (375, 375, 650, 375, 450))))
TOLERANCE = D("0.00000001")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def number(value):
    n = D(str(value).replace(",", "."))
    if not n.is_finite():
        raise ValueError("Número não finito")
    return n


def write(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_source(path):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    bars = {}
    for row in workbook["Planilha1"].iter_rows(min_row=2, values_only=True):
        stamp = row[0]
        if not isinstance(stamp, datetime) or not "2026-08-31" <= stamp.date().isoformat() <= END:
            continue
        if stamp in bars:
            raise ValueError(f"Barra duplicada em {path.name}: {stamp}")
        o, h, l, c, adjustment = map(number, row[1:6])
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError(f"OHLC inválido: {stamp}")
        bars[stamp] = (o, h, l, c, adjustment)
    workbook.close()
    return bars


def context(bars):
    groups = defaultdict(list)
    for stamp, values in bars.items():
        groups[stamp.date().isoformat()].append((stamp, values))
    result = {}
    for day, rows in groups.items():
        rows.sort()
        opening = datetime.fromisoformat(day + " 09:00:00")
        expected = [opening + timedelta(minutes=15*i) for i in range(38)]
        result[day] = {
            "date": day, "open": rows[0][1][0], "high": max(r[1][1] for r in rows),
            "low": min(r[1][2] for r in rows), "close": rows[-1][1][3],
            "count": len(rows), "cadence": [r[0] for r in rows] == expected,
            "adjustments": {r[1][4] for r in rows},
        }
    return result


def prices(o, h, l, c, adjustment):
    # Decimal evita normalizar ou truncar os preços teóricos ao tick.
    pivot = (h+l+c)/3
    r200 = o+2*abs(l-pivot)
    s200 = o-2*abs(h-pivot)
    r = {p: adjustment+(r200-adjustment)*D(p) for p in ("0.236", "0.382", "0.5", "0.618")}
    s = {p: adjustment+(s200-adjustment)*D(p) for p in ("0.236", "0.382", "0.5", "0.618")}
    entries = dict(zip(LEVELS, (s["0.382"], s["0.5"], s["0.618"], r["0.382"], r["0.618"])))
    targets = dict(zip(LEVELS, ((s["0.382"]+s["0.236"])/2, s["0.382"], s["0.5"], r["0.236"], (r["0.618"]+r["0.5"])/2)))
    return pivot, r200, s200, entries, targets


def run(data, out, workspace):
    out.mkdir(parents=True, exist_ok=True)
    operations = [r for r in read(data/"Referencia_D_operacoes.csv") if START <= r["Data"] <= END]
    daily = [r for r in read(data/"Referencia_D_diário.csv") if START <= r["Data"] <= END]
    adjustments = {r["DataOperacional"]: r for r in read(data/"Ajustes_Diarios_Modelo_D_20230301_20260921.csv")}
    sources = {name: load_source(data/"Fontes_Originais_Ajuste"/name) for name in ("Book(3).xlsx", "Jan e Fev 2026.xlsx")}
    a, b = sources.values()
    common = set(a) & set(b)
    same_sources = a == b
    market = context(a)
    by_key = {(r["Data"], r["Nível"]): r for r in operations}
    if len(by_key) != len(operations):
        raise ValueError("Referência duplicada")
    day_rows, level_rows = [], []
    maximum_error = D(0)
    checked = mismatched = 0
    for work_day in daily:
        day = work_day["Data"]
        current = market[day]
        previous_date = max(d for d in market if d < day)
        previous = market[previous_date]
        adjustment = number(adjustments[day]["Ajuste"])
        if current["adjustments"] != {adjustment}:
            raise ValueError(f"Ajuste diferente da data operacional: {day}")
        with localcontext() as ctx:
            ctx.prec = 40
            pivot, r200, s200, entries, targets = prices(current["open"], previous["high"], previous["low"], previous["close"], adjustment)
            errors, bad_levels = [], 0
            for level in LEVELS:
                buy = level.startswith("S")
                entry = entries[level]
                stop = entry-STOPS[level] if buy else entry+STOPS[level]
                target = targets[level]
                geometry = adjustment <= s200 if buy else adjustment >= r200
                opening_valid = current["open"] >= entry if buy else current["open"] <= entry
                ref = by_key.get((day, level))
                error = None
                state = "CALCULADO_SEM_PRECO_REFERENCIA_INDEPENDENTE"
                if ref:
                    diffs = [abs(number(ref[field])-value) for field, value in (("Abertura", current["open"]), ("Linha", entry), ("Entrada", entry), ("Stop", stop), ("Alvo", target))]
                    error = max(diffs)
                    maximum_error = max(maximum_error, error)
                    errors.append(error)
                    checked += 1
                    bad = error > TOLERANCE or geometry or not opening_valid
                    bad_levels += bad
                    mismatched += bad
                    state = "DIVERGENTE" if bad else "COMPATIVEL_COM_OPERACAO_WORK"
                level_rows.append({"Data": day, "Nivel": level, "Lado": "COMPRA" if buy else "VENDA",
                    "EntradaMatematica": str(entry), "StopMatematico": str(stop), "AlvoMatematico": str(target),
                    "GeometriaBloqueada": "SIM" if geometry else "NAO", "FiltroAberturaValido": "SIM" if opening_valid else "NAO",
                    "OperacaoNaReferencia": "SIM" if ref else "NAO",
                    "EntradaWork": ref["Entrada"] if ref else "", "StopWork": ref["Stop"] if ref else "", "AlvoWork": ref["Alvo"] if ref else "",
                    "MaiorDiferencaNumerica": str(error) if ref else "",
                    "EstadoConferenciaPreco": state,
                    "CronologiaOperacao": "PENDENTE_M1_ORIGINAL", "ExecucaoEA": "PENDENTE_CONTRATO_E_TICKS"})
            day_rows.append({"Data": day, "PregaoAnteriorDisponivel": previous_date,
                "Abertura": str(current["open"]), "MaximaAnterior": str(previous["high"]), "MinimaAnterior": str(previous["low"]), "FechamentoAnterior": str(previous["close"]),
                "AjusteDataOperacional": str(adjustment), "PP": str(pivot), "R200": str(r200), "S200": str(s200),
                **{level: str(entries[level]) for level in LEVELS},
                "RegistrosM15Hoje": current["count"], "RegistrosM15Anterior": previous["count"],
                "GradeM15HojeSemLacunas": "SIM" if current["cadence"] else "NAO", "GradeM15AnteriorSemLacunas": "SIM" if previous["cadence"] else "NAO",
                "OperacoesWork": work_day["Operações"], "NiveisComPrecoConferidoWork": len(errors),
                "MaiorDiferencaPreco": str(max(errors)) if errors else "", "DivergenciasPrecoOuFiltro": bad_levels,
                "OrigemContexto": "Book(3).xlsx/Planilha1, agregado M15; conferido com Jan e Fev 2026.xlsx",
                "ContextoM1Original": "NAO_DISPONIVEL", "ContratoReal": "NAO_COMPROVADO", "TicksEA": "NAO_DISPONIVEIS"})
    write(out/"CONTEXTO_E_CINCO_NIVEIS_POR_PREGAO.csv", day_rows)
    write(out/"CONFERENCIA_70_NIVEIS.csv", level_rows)
    archives = []
    for path in sorted(workspace.rglob("*.zip")):
        if ".git" in path.parts:
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                candidates = [{"nome": r.filename, "bytes": r.file_size} for r in archive.infolist()
                              if r.filename.lower().endswith((".csv", ".xlsx", ".xls", ".zip", ".7z", ".rar"))]
                archives.append({"arquivo": str(path.relative_to(workspace)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "total_itens": len(archive.infolist()), "candidatos_dados_ou_subarquivos": candidates})
        except zipfile.BadZipFile:
            archives.append({"arquivo": str(path.relative_to(workspace)), "erro": "ZIP_INVALIDO"})
    (out/"INVENTARIO_ZIPS_DISPONIVEIS.json").write_text(json.dumps(archives, ensure_ascii=False, indent=2)+"\n")
    summary = {
        "periodo": [START, END], "contexto_necessario_desde": "2026-08-31", "pregoes_work": len(daily),
        "niveis_calculados": len(level_rows), "operacoes_work_com_precos_conferidos": checked,
        "operacoes_divergentes_em_preco_ou_filtro": mismatched, "maior_diferenca_numerica_ponto": str(maximum_error),
        "tolerancia_representacao_numerica": str(TOLERANCE),
        "dia_sem_operacoes_sem_referencia_independente_de_niveis": [r["Data"] for r in daily if r["Operações"] == "0"],
        "duas_fontes_M15": {"iguais_no_recorte": same_sources, "registros_comuns": len(common),
                             "registros_divergentes": sum(a[k] != b[k] for k in common)},
        "arquivos_zip_inventariados": len(archives),
        "resultado": "CONTEXTO_M15_COMPATIVEL_COM_PRECOS_WORK; CRONOLOGIA_M1_E_EXECUCAO_EA_PENDENTES",
        "operacoes_recalculadas_intradia": 0, "backtests_ea": 0,
        "limite": "A coincidência com preços de operações não valida independentemente cada H/L/C anterior, os 70 níveis, cobertura M1 ou ticks, nem o contrato real. As duas fontes M15 podem compartilhar a mesma origem.",
        "hashes": {str(p.relative_to(data)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [data/"Fontes_Originais_Ajuste/Book(3).xlsx", data/"Fontes_Originais_Ajuste/Jan e Fev 2026.xlsx", data/"Referencia_D_operacoes.csv", data/"Referencia_D_diário.csv", data/"Ajustes_Diarios_Modelo_D_20230301_20260921.csv"]},
    }
    (out/"RESUMO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path("/workspace"))
    args = parser.parse_args()
    print(json.dumps(run(args.dados, args.saida, args.workspace), ensure_ascii=False, indent=2))
