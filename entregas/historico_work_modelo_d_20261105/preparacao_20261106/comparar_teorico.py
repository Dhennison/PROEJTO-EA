"""Compara uma NOVA rotina teórica com o Work; nunca converte referência em execução MT5.

Operações: mesmo cabeçalho do CSV canônico. Cobertura: Data;Estado, com
Estado=PROCESSADO somente após a rotina independente concluir o pregão inteiro.
Um dia processado sem linhas de operações significa zero operações; um dia ausente
da cobertura permanece pendente, sem ser contado como zero.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date, time
from decimal import Decimal
from pathlib import Path

LEVELS = {"S38.2": "COMPRA", "S50": "COMPRA", "S61.8": "COMPRA", "R38.2": "VENDA", "R61.8": "VENDA"}
NUMBERS = ("Abertura", "Linha", "Entrada", "Stop", "Alvo", "Saída", "Pontos")
TEXT = ("Hora entrada", "Hora saída", "Motivo", "Ambíguo", "Zeragem")
KEYS = ("Data", "Nível", "Lado")
TOLERANCE = Decimal("0.000001")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def number(value):
    result = Decimal(value.replace(",", "."))
    if not result.is_finite():
        raise ValueError("Número não finito")
    return result


def indexed(rows):
    result = {}
    for row in rows:
        date.fromisoformat(row["Data"])
        if LEVELS.get(row["Nível"]) != row["Lado"]:
            raise ValueError("Nível/lado inválido")
        for field in NUMBERS:
            number(row[field])
        for field in ("Hora entrada", "Hora saída", "Zeragem"):
            time.fromisoformat(row[field])
        if row["Motivo"] not in {"ALVO", "STOP", "ZERAGEM 17:45", "ZERAGEM 18H"}:
            raise ValueError("Motivo desconhecido")
        if row["Ambíguo"] not in {"", "SIM"}:
            raise ValueError("Marcador de ambiguidade inválido")
        key = tuple(row[field] for field in KEYS)
        if key in result:
            raise ValueError(f"Operação duplicada: {key}")
        result[key] = row
    return result


def compare(reference, actual, eligible, coverage):
    if len(eligible) != len(set(eligible)):
        raise ValueError("Pregões elegíveis duplicados")
    universe = set(eligible)
    done = set()
    for row in coverage:
        if row["Estado"] != "PROCESSADO" or row["Data"] not in universe or row["Data"] in done:
            raise ValueError("Cobertura inválida, duplicada ou fora do universo")
        done.add(row["Data"])
    ref, new = indexed(reference), indexed(actual)
    if any(key[0] not in universe for key in ref) or any(key[0] not in done for key in new):
        raise ValueError("Operação fora do universo ou sem cobertura concluída")
    diffs = []
    for key in sorted(k for k in set(ref) | set(new) if k[0] in done):
        old, latest = ref.get(key), new.get(key)
        changed = []
        if old and latest:
            changed = [f for f in NUMBERS if abs(number(old[f]) - number(latest[f])) > TOLERANCE]
            changed += [f for f in TEXT if old[f] != latest[f]]
        status = "EXTRA_NOVA_ROTINA" if not old else "AUSENTE_NOVA_ROTINA" if not latest else "DIVERGENTE" if changed else "COMPATIVEL"
        diffs.append(dict(zip(KEYS, key)) | {"Estado": status, "CamposDiferentes": ", ".join(changed),
                     "PontosWork": old["Pontos"] if old else "", "PontosNovaRotina": latest["Pontos"] if latest else ""})
    days = []
    work_balance = new_balance = work_peak = new_peak = work_dd = new_dd = Decimal(0)
    totals = defaultdict(lambda: {"PontosWork": Decimal(0), "PontosNovaRotina": Decimal(0), "Pregoes": 0})
    for day in sorted(done):
        w = sum((number(r["Pontos"]) for k, r in ref.items() if k[0] == day), Decimal(0))
        n = sum((number(r["Pontos"]) for k, r in new.items() if k[0] == day), Decimal(0))
        work_balance += w
        new_balance += n
        work_peak = max(work_peak, work_balance)
        new_peak = max(new_peak, new_balance)
        work_dd = max(work_dd, work_peak - work_balance)
        new_dd = max(new_dd, new_peak - new_balance)
        days.append({"Data": day, "PontosWork": str(w), "PontosNovaRotina": str(n), "Diferenca": str(n-w)})
        for period in (day[:4], day[:7], "TOTAL"):
            totals[period]["PontosWork"] += w
            totals[period]["PontosNovaRotina"] += n
            totals[period]["Pregoes"] += 1
    summary = {
        "estado": "SEM_NOVA_EXECUCAO" if not done else "COMPLETO" if done == universe else "PARCIAL",
        "camada": "TEORICA_INDEPENDENTE", "pregoes_comparados": len(done), "pregoes_pendentes": sorted(universe-done),
        "divergencias": sum(r["Estado"] != "COMPATIVEL" for r in diffs),
        "dd_work_sequencia_datas_processadas": str(work_dd), "dd_nova_sequencia_datas_processadas": str(new_dd),
        "dd_periodo_integral_certificado": done == universe and bool(done),
        "tolerancia_numerica_ponto": str(TOLERANCE),
        "limite": "Não compara fills/parciais do MT5. Em cobertura parcial, totais e DD referem-se apenas às datas processadas, não ao período inteiro.",
    }
    return summary, diffs, days, [{"Periodo": k, **{f: str(v) for f, v in value.items()}} for k, value in sorted(totals.items())]


def save_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("referencia", "operacoes", "diario", "cobertura", "saida"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    summary, diffs, days, totals = compare(read(args.referencia), read(args.operacoes),
                                         [r["Data"] for r in read(args.diario)], read(args.cobertura))
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "RESUMO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    save_csv(args.saida / "POR_OPERACAO.csv", (*KEYS, "Estado", "CamposDiferentes", "PontosWork", "PontosNovaRotina"), diffs)
    save_csv(args.saida / "POR_DIA.csv", ("Data", "PontosWork", "PontosNovaRotina", "Diferenca"), days)
    save_csv(args.saida / "POR_PERIODO.csv", ("Periodo", "PontosWork", "PontosNovaRotina", "Pregoes"), totals)
    print(json.dumps({k: v for k, v in summary.items() if k != "pregoes_pendentes"}, ensure_ascii=False, indent=2))
