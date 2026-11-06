"""Replay independente por candles originais do Work, exclusivamente Modelo D.

Não executa o EA nem simula a fila de ordens. Sem preços da referência como entrada.
"""
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal as D, ROUND_HALF_EVEN, localcontext
from pathlib import Path

LEVELS = ("S38.2", "S50", "S61.8", "R38.2", "R61.8")
STOPS = dict(zip(LEVELS, map(D, (375, 375, 650, 375, 450))))
FIELDS = ("Data", "Nível", "Lado", "Abertura", "Linha", "Hora entrada", "Entrada", "Stop", "Alvo", "Hora saída", "Saída", "Motivo", "Pontos", "Ambíguo", "Zeragem")


@dataclass(frozen=True)
class Bar:
    stamp: datetime
    o: D
    h: D
    l: D
    c: D


def number(text, profit=False):
    result = D(text.replace(".", "").replace(",", ".") if profit else text)
    if not result.is_finite():
        raise ValueError("Número não finito")
    return result


def parse_bars(name, raw):
    mt5 = name.startswith("WIN$N")
    rows = csv.reader(io.StringIO(raw.decode("utf-8-sig" if mt5 else "cp1252")), delimiter="\t" if mt5 else ";")
    bars, seen = [], set()
    for idx, row in enumerate(rows):
        if not row:
            continue
        if idx == 0 and row[0] in ("<DATE>", "Ativo"):
            continue
        if mt5:
            stamp = datetime.strptime(" ".join(row[:2]), "%Y.%m.%d %H:%M:%S")
            prices = row[2:6]
        else:
            if row[0] != "WINFUT":
                raise ValueError(f"Símbolo inesperado: {name}: {row[0]}")
            stamp = datetime.strptime(" ".join(row[1:3]), "%d/%m/%Y %H:%M:%S")
            prices = row[3:7]
        if stamp in seen:
            raise ValueError(f"Barra duplicada: {name}: {stamp}")
        seen.add(stamp)
        bar = Bar(stamp, *(number(v, not mt5) for v in prices))
        if not bar.l <= min(bar.o, bar.c) <= max(bar.o, bar.c) <= bar.h:
            raise ValueError(f"OHLC inválido: {name}: {stamp}")
        bars.append(bar)
    if not bars:
        raise ValueError(f"Sem barras: {name}")
    return sorted(bars, key=lambda b: b.stamp)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def calculate(o, h, l, c, adjustment):
    pp = (h+l+c)/3
    r200, s200 = o+2*abs(l-pp), o-2*abs(h-pp)
    r = {p: adjustment+(r200-adjustment)*D(p) for p in ("0.236", "0.382", "0.5", "0.618")}
    s = {p: adjustment+(s200-adjustment)*D(p) for p in ("0.236", "0.382", "0.5", "0.618")}
    entries = dict(zip(LEVELS, (s["0.382"], s["0.5"], s["0.618"], r["0.382"], r["0.618"])))
    targets = dict(zip(LEVELS, ((s["0.382"]+s["0.236"])/2, s["0.382"], s["0.5"], r["0.236"], (r["0.618"]+r["0.5"])/2)))
    return pp, r200, s200, entries, targets


def replay_day(bars, previous, adjustment, cutoff):
    """Primeiro toque por candle; testa saída na vela de entrada e STOP FIRST."""
    if not bars or not previous:
        raise ValueError("Dia/contexto vazio")
    opening = bars[0].o
    day = bars[0].stamp.date().isoformat()
    if bars[0].stamp.time().isoformat() < "09:00:00":
        raise ValueError("Barras anteriores à abertura regular não autorizadas neste replay")
    cut_stamp = datetime.fromisoformat(day+" "+cutoff)
    cuts = [b for b in bars if b.stamp == cut_stamp]
    if len(cuts) != 1:
        raise ValueError(f"Falta barra exata do corte: {day}")
    _, r200, s200, entries, targets = calculate(opening, max(b.h for b in previous), min(b.l for b in previous), previous[-1].c, adjustment)
    result, states = [], []
    for level in LEVELS:
        buy = level.startswith("S")
        entry, target = entries[level], targets[level]
        stop = entry-STOPS[level] if buy else entry+STOPS[level]
        geometry = adjustment <= s200 if buy else adjustment >= r200
        valid_open = opening >= entry if buy else opening <= entry
        entered = None
        reason = exit_price = exit_stamp = None
        ambiguous = ""
        if not geometry and valid_open:
            for bar in bars:
                if bar.stamp >= cut_stamp:
                    break
                if entered is None:
                    if not (bar.l <= entry if buy else bar.h >= entry):
                        continue
                    entered = bar.stamp
                stop_hit = bar.l <= stop if buy else bar.h >= stop
                target_hit = bar.h >= target if buy else bar.l <= target
                if stop_hit or target_hit:
                    ambiguous = "SIM" if stop_hit and target_hit else ""
                    reason = "STOP" if stop_hit else "ALVO"
                    exit_price = stop if stop_hit else target
                    exit_stamp = bar.stamp
                    break
            if entered is not None and reason is None:
                reason = "ZERAGEM 17:45" if cutoff == "17:45:00" else "ZERAGEM 18H"
                exit_price, exit_stamp = cuts[0].o, cut_stamp
        state = "GEOMETRIA_BLOQUEADA" if geometry else "ABERTURA_INVALIDA" if not valid_open else "OPERACAO_TEORICA" if entered is not None else "SEM_TOQUE_ANTES_CORTE"
        states.append({"Data": day, "Nivel": level, "Entrada": str(entry), "Stop": str(stop), "Alvo": str(target), "Estado": state})
        if entered is None:
            continue
        points = (exit_price-entry if buy else entry-exit_price).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)
        result.append(dict(zip(FIELDS, (day, level, "COMPRA" if buy else "VENDA", str(opening), str(entry), entered.time().isoformat(), str(entry), str(stop), str(target), exit_stamp.time().isoformat(), str(exit_price), reason, str(points), ambiguous, cutoff))))
    return result, states


def run(archive, reference_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    by_source, inventory = {}, []
    with zipfile.ZipFile(archive) as z:
        guide = z.read("LEIA_FONTE_CANDLES.txt").decode("utf-8-sig")
        for name in z.namelist():
            if not name.endswith(".csv"):
                continue
            raw = z.read(name)
            digest = hashlib.sha256(raw).hexdigest()
            if f"{name} {digest}" not in guide:
                raise ValueError(f"Hash não confere com o guia: {name}")
            bars = parse_bars(name, raw)
            by_source[name] = bars
            inventory.append({"arquivo": name, "sha256": digest, "bytes": len(raw), "barras": len(bars),
                              "primeiro": bars[0].stamp.isoformat(), "ultimo": bars[-1].stamp.isoformat(),
                              "pregoes": len({b.stamp.date() for b in bars}), "simbolo": "WIN$N" if name.startswith("WIN$N") else "WINFUT",
                              "tempo_grafico": "M1" if "1min" in name else "M5", "duplicidades": 0, "OHLC_invalidos": 0})
    (out/"INVENTARIO_ORIGINAIS.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n")
    all_daily = read_csv(reference_dir/"Referencia_D_diário.csv")
    adjustments = {r["DataOperacional"]: r for r in read_csv(reference_dir/"Ajustes_Diarios_Modelo_D_20230301_20260921.csv")}
    source_days = {}
    for name, sequence in by_source.items():
        groups = defaultdict(list)
        for bar in sequence:
            groups[bar.stamp.date().isoformat()].append(bar)
        source_days[name] = groups
    date_inventory = []
    for record in all_daily:
        day = record["Data"]
        if day[:4] == "2023":
            source = next(n for n in by_source if n.startswith("WIN$N"))
        elif day < "2026-03-01":
            source = next(n for n in by_source if f"01-01-{day[:4]}" in n and "5min" in n)
        else:
            source = next(n for n in by_source if "1min" in n)
        sequence = source_days[source].get(day, [])
        cutoff = adjustments[day]["ZeragemComparacaoWork"]
        date_inventory.append({"Data": day, "Arquivo": source, "Barras": len(sequence),
                               "PrimeiraBarra": sequence[0].stamp.time().isoformat() if sequence else "",
                               "UltimaBarra": sequence[-1].stamp.time().isoformat() if sequence else "",
                               "BarraDoCortePresente": "SIM" if any(b.stamp.time().isoformat() == cutoff for b in sequence) else "NAO",
                               "Replay": "PROCESSADO" if "2026-09-01" <= day <= "2026-09-21" else "PENDENTE"})
    write_csv(out/"PRESENCA_CANDLES_877_DATAS.csv", date_inventory[0].keys(), date_inventory)
    selected_name = "WINFUT_F_0_1min_01-01-2026_22-09-2026.csv"
    by_day = defaultdict(list)
    for bar in by_source[selected_name]:
        by_day[bar.stamp.date().isoformat()].append(bar)
    universe = [r["Data"] for r in read_csv(reference_dir/"Referencia_D_diário.csv") if "2026-09-01" <= r["Data"] <= "2026-09-21"]
    output, states, contexts, coverage = [], [], [], []
    for day in universe:
        bars = by_day[day]
        previous_day = max(d for d in by_day if d < day)
        prev = by_day[previous_day]
        gaps = []
        for segment, sequence in (("HOJE", bars), ("ANTERIOR", prev)):
            gaps.extend(f"{segment}:{a.stamp.isoformat()}->{b.stamp.isoformat()}" for a, b in zip(sequence, sequence[1:]) if b.stamp-a.stamp != timedelta(minutes=1))
        if gaps:
            raise ValueError(f"Lacunas internas M1 {day}: {gaps}")
        adjustment = number(adjustments[day]["Ajuste"].replace(",", "."))
        cutoff = adjustments[day]["ZeragemComparacaoWork"]
        with localcontext() as ctx:
            ctx.prec = 40
            operations, levels = replay_day(bars, prev, adjustment, cutoff)
            pp, r2, s2, entries, _ = calculate(bars[0].o, max(b.h for b in prev), min(b.l for b in prev), prev[-1].c, adjustment)
        output.extend(operations)
        states.extend(levels)
        coverage.append({"Data": day, "Estado": "PROCESSADO"})
        contexts.append({"Data": day, "PregaoAnterior": previous_day, "Abertura": str(bars[0].o),
                         "MaximaAnterior": str(max(b.h for b in prev)), "MinimaAnterior": str(min(b.l for b in prev)), "FechamentoAnterior": str(prev[-1].c),
                         "Ajuste": str(adjustment), "PP": str(pp), "R200": str(r2), "S200": str(s2), **{k: str(v) for k, v in entries.items()},
                         "PrimeiraBarra": bars[0].stamp.time().isoformat(), "UltimaBarra": bars[-1].stamp.time().isoformat(),
                         "BarrasM1Hoje": len(bars), "BarrasM1Anterior": len(prev), "LacunasInternas": len(gaps), "Corte": cutoff})
    write_csv(out/"OPERACOES_REPLAY_D.csv", FIELDS, output)
    write_csv(out/"COBERTURA_REPLAY.csv", ("Data", "Estado"), coverage)
    write_csv(out/"CONTEXTO_M1_E_CINCO_NIVEIS.csv", contexts[0].keys(), contexts)
    write_csv(out/"ESTADO_70_NIVEIS.csv", states[0].keys(), states)
    summary = {"camada": "REPLAY_TEORICO_CANDLES_ORIGINAIS", "fonte": selected_name, "simbolo": "WINFUT", "tempo_grafico": "M1",
               "periodo": [min(universe), max(universe)], "pregoes": len(universe), "operacoes": len(output),
               "pontos_por_contrato": str(sum((D(r["Pontos"]) for r in output), D(0))),
               "motivos": dict(Counter(r["Motivo"] for r in output)), "estados_niveis": dict(Counter(r["Estado"] for r in states)),
               "sem_operacoes": sorted(set(universe)-{r["Data"] for r in output}), "hash_zip": hashlib.sha256(archive.read_bytes()).hexdigest(),
               "inventario_877_datas": {"datas_sem_candles": [r["Data"] for r in date_inventory if not r["Barras"]],
                                        "datas_sem_barra_corte": [r["Data"] for r in date_inventory if r["BarraDoCortePresente"] != "SIM"],
                                        "limite": "Presença de barras/corte não certifica cobertura integral ou replay dos demais pregões."},
               "regra": "Entrada teórica na linha; STOP FIRST intrabar; saída pelo OPEN do corte; sem custos, arredondamento ao tick ou slippage.",
               "limite": "Não é execução do EA/MT5. Ausência de barras antes da primeira barra original não certifica horário do primeiro negócio por ticks."}
    (out/"RESUMO_REPLAY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("referencias", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.zip, args.referencias, args.saida), ensure_ascii=False, indent=2))
