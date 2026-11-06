"""Ampliação do replay teórico aos 877 pregões; sem alteração do EA instalado."""
import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal as D, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"replay_setembro_20261106"))
from replay import FIELDS, calculate, parse_bars, read_csv, replay_day, write_csv


def select_source(day, names):
    if day[:4] == "2023":
        return next(n for n in names if n.startswith("WIN$N"))
    if day < "2026-03-01":
        return next(n for n in names if f"01-01-{day[:4]}" in n and "5min" in n)
    return next(n for n in names if "1min" in n)


def cutoff_for(day):
    return "17:45:00" if "2023-03-13" <= day <= "2023-11-03" else "18:00:00"


def run(archive, reference_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    source_days, source_hashes = {}, {}
    with zipfile.ZipFile(archive) as z:
        guide = z.read("LEIA_FONTE_CANDLES.txt").decode("utf-8-sig")
        for name in z.namelist():
            if not name.endswith(".csv"):
                continue
            raw = z.read(name)
            digest = hashlib.sha256(raw).hexdigest()
            if f"{name} {digest}" not in guide:
                raise ValueError(f"Hash do CSV não confere: {name}")
            source_hashes[name] = digest
            days = defaultdict(list)
            for bar in parse_bars(name, raw):
                days[bar.stamp.date().isoformat()].append(bar)
            source_days[name] = days
    universe = [r["Data"] for r in read_csv(reference_dir/"Referencia_D_diário.csv")]
    if len(universe) != len(set(universe)) or universe != sorted(universe):
        raise ValueError("Universo repetido ou desordenado")
    adjustments = {r["DataOperacional"]: r for r in read_csv(reference_dir/"Ajustes_Diarios_Modelo_D_20230301_20260921.csv")}
    market_dates = sorted({d for groups in source_days.values() for d in groups})
    output, states, contexts, coverage, gaps = [], [], [], [], []
    for day in universe:
        source = select_source(day, source_days)
        bars = source_days[source][day]
        previous_day = max(d for d in market_dates if d < day)
        # Contexto escolhe a fonte pelo dia anterior: 30/12/2025 M5 para 02/01/2026;
        # 27/02/2026 M5 completo para 02/03/2026, sem usar o M1 parcial sobreposto.
        previous_source = select_source(previous_day, source_days)
        previous = source_days[previous_source][previous_day]
        if not bars or not previous:
            raise ValueError(f"Contexto indisponível: {day}")
        for scope, sequence, origin in (("ATUAL", bars, source), ("ANTERIOR", previous, previous_source)):
            step = timedelta(minutes=1 if "1min" in origin else 5)
            for a, b in zip(sequence, sequence[1:]):
                if b.stamp-a.stamp != step:
                    gaps.append({"DataOperacional": day, "Escopo": scope, "Arquivo": origin, "De": a.stamp.isoformat(), "Ate": b.stamp.isoformat(), "PassoEsperadoSegundos": int(step.total_seconds())})
        adjustment = D(adjustments[day]["Ajuste"].replace(",", "."))
        cutoff = cutoff_for(day)
        if adjustments[day]["ZeragemComparacaoWork"] != cutoff:
            raise ValueError(f"Cutoff divergente do calendário aprovado: {day}")
        with localcontext() as ctx:
            ctx.prec = 40
            operations, levels = replay_day(bars, previous, adjustment, cutoff)
            pp, r200, s200, entries, _ = calculate(bars[0].o, max(b.h for b in previous), min(b.l for b in previous), previous[-1].c, adjustment)
        output.extend(operations)
        states.extend(levels)
        coverage.append({"Data": day, "Estado": "PROCESSADO"})
        contexts.append({"Data": day, "ArquivoAtual": source, "PregaoAnterior": previous_day, "ArquivoAnterior": previous_source,
                         "Abertura": str(bars[0].o), "MaximaAnterior": str(max(b.h for b in previous)), "MinimaAnterior": str(min(b.l for b in previous)), "FechamentoAnterior": str(previous[-1].c),
                         "Ajuste": str(adjustment), "PP": str(pp), "R200": str(r200), "S200": str(s200), **{k: str(v) for k, v in entries.items()},
                         "PrimeiraBarra": bars[0].stamp.time().isoformat(), "UltimaBarra": bars[-1].stamp.time().isoformat(), "Barras": len(bars), "Corte": cutoff})
    write_csv(out/"OPERACOES_REPLAY_D.csv", FIELDS, output)
    write_csv(out/"COBERTURA_REPLAY.csv", ("Data", "Estado"), coverage)
    write_csv(out/"CONTEXTO_E_4385_NIVEIS.csv", contexts[0].keys(), contexts)
    write_csv(out/"ESTADOS_4385_NIVEIS.csv", states[0].keys(), states)
    write_csv(out/"LACUNAS_INTERNAS_OBSERVADAS.csv", ("DataOperacional", "Escopo", "Arquivo", "De", "Ate", "PassoEsperadoSegundos"), gaps)
    ambiguous = [r for r in output if r["Ambíguo"] == "SIM"]
    write_csv(out/"AMBIGUIDADES_REPLAY_STOP_FIRST.csv", FIELDS, ambiguous)
    summary = {"camada": "REPLAY_TEORICO_CANDLES_ORIGINAIS", "periodo": [min(universe), max(universe)],
               "pregoes": len(universe), "operacoes": len(output), "niveis": len(states),
               "pontos_por_contrato": str(sum((D(r["Pontos"]) for r in output), D(0))),
               "por_ano": {year: {"operacoes": sum(r["Data"].startswith(year) for r in output),
                                   "pontos": str(sum((D(r["Pontos"]) for r in output if r["Data"].startswith(year)), D(0)))} for year in sorted({d[:4] for d in universe})},
               "motivos": dict(Counter(r["Motivo"] for r in output)), "estados_niveis": dict(Counter(r["Estado"] for r in states)),
               "pregoes_sem_operacao": len(set(universe)-{r["Data"] for r in output}),
               "operacoes_ambiguas": len(ambiguous), "pregoes_com_ambiguidade": len({r["Data"] for r in ambiguous}),
               "registros_lacunas_internas": len(gaps), "dias_contexto_troca_fonte": [r["Data"] for r in contexts if r["ArquivoAtual"] != r["ArquivoAnterior"]],
               "hashes_csv_brutos": source_hashes,
               "limite": "Reprodução teórica STOP FIRST; lacunas não preenchidas. Não é execução MT5 nem certificado de ticks reais."}
    (out/"RESUMO_REPLAY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("referencias", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.zip, args.referencias, args.saida), ensure_ascii=False, indent=2))
