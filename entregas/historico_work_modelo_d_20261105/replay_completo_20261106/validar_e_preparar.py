"""Conferência adicional exata dos resultados e fila de ambiguidades para ticks."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"replay_setembro_20261106"))
from replay import read_csv, write_csv
from replay_completo import select_source


def number(value):
    return D(value.replace(",", "."))


def validate(reference_dir, results):
    ops = read_csv(results/"OPERACOES_REPLAY_D.csv")
    refs = read_csv(reference_dir/"Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv")
    daily = read_csv(reference_dir/"Referencia_D_diário.csv")
    contexts = {r["Data"]: r for r in read_csv(results/"CONTEXTO_E_4385_NIVEIS.csv")}
    key = lambda r: (r["Data"], r["Nível"], r["Lado"])
    original = {key(r): r for r in refs}
    counts = Counter(r["Data"] for r in ops)
    by_day = defaultdict(lambda: D(0))
    for row in ops:
        by_day[row["Data"]] += number(row["Pontos"])
    prefix = [D(0)]
    peak = D(0)
    curve_ok = True
    for day in daily:
        prefix.append(prefix[-1]+by_day[day["Data"]])
        peak = max(peak, prefix[-1])
        curve_ok &= prefix[-1] == number(day["Acumulado"]) and peak == number(day["Pico acumulado"]) and peak-prefix[-1] == number(day["Drawdown"])
    # Segundo cálculo de DD: máximo de todos os prefixos anteriores a cada ponto.
    independent_dd = max(max(prefix[:j+1])-value for j, value in enumerate(prefix))
    checks = {
        "877_pregoes": len(daily) == 877 == len(contexts),
        "1877_operacoes_chaves_exatas": len(ops) == len(original) == 1877 and {key(r) for r in ops} == set(original),
        "pontos_exatos_em_cada_operacao_sem_tolerancia": all(number(r["Pontos"]) == number(original[key(r)]["Pontos"]) for r in ops),
        "contagem_e_pontos_exatos_cada_dia": all(counts[d["Data"]] == int(d["Operações"]) and by_day[d["Data"]] == number(d["Pontos"]) for d in daily),
        "curva_pico_dd_diarios_exatos": bool(curve_ok),
        "dd_independente": independent_dd == D("4780.240329"),
        "soma_exata": prefix[-1] == D("124337.758661"),
        "112_pregoes_sem_operacao": sum(counts[d["Data"]] == 0 for d in daily) == 112,
        "contexto_20260102_20251230_M5": contexts["2026-01-02"]["PregaoAnterior"] == "2025-12-30" and "5min" in contexts["2026-01-02"]["ArquivoAnterior"],
        "contexto_20260302_20260227_M5_completo": contexts["2026-03-02"]["PregaoAnterior"] == "2026-02-27" and "5min" in contexts["2026-03-02"]["ArquivoAnterior"] and "1min" in contexts["2026-03-02"]["ArquivoAtual"],
        "limites_cutoff_2023": contexts["2023-03-10"]["Corte"] == "18:00:00" and contexts["2023-03-13"]["Corte"] == "17:45:00" and contexts["2023-11-03"]["Corte"] == "17:45:00" and contexts["2023-11-06"]["Corte"] == "18:00:00",
    }
    ambiguous = [r for r in ops if r["Ambíguo"] == "SIM"]
    checks["32_ambiguidades_mesmas_chaves_work"] = len(ambiguous) == 32 and {key(r) for r in ambiguous} == {key(r) for r in refs if r["Ambíguo"] == "SIM"}
    checks["26_pregoes_ambiguos"] = len({r["Data"] for r in ambiguous}) == 26
    queue = []
    for row in ambiguous:
        context = contexts[row["Data"]]
        step = 1 if "1min" in context["ArquivoAtual"] else 5
        entry = datetime.fromisoformat(row["Data"]+" "+row["Hora entrada"])
        exit_bar = datetime.fromisoformat(row["Data"]+" "+row["Hora saída"])
        queue.append({"Data": row["Data"], "Nivel": row["Nível"], "Lado": row["Lado"],
                      "SimboloReferencia": "WIN$N" if context["ArquivoAtual"].startswith("WIN$N") else "WINFUT",
                      "TempoGraficoWork": "M1" if step == 1 else "M5", "ArquivoReferencia": context["ArquivoAtual"],
                      "Entrada": row["Entrada"], "Stop": row["Stop"], "Alvo": row["Alvo"],
                      "VelaEntrada": entry.isoformat(), "VelaAmbigua": exit_bar.isoformat(),
                      "FimVelaAmbiguaExclusivo": (exit_bar+timedelta(minutes=step)).isoformat(),
                      "InicioRecorteDiagnostico": (entry-timedelta(minutes=step)).isoformat(),
                      "ResultadoWork": row["Motivo"], "PontosWork": row["Pontos"],
                      "ContratoRealConfirmado": "", "CoberturaTicksReais": "PENDENTE",
                      "PrimeiroEventoPorTicks": "", "SaidaNativaMT5": "", "EstadoComparativo": "PENDENTE_TICKS_E_EXECUCAO",
                      "RegraMT5": "CRONOLOGIA_OBSERVADA; SEM_STOP_FIRST_AUTOMATICO"})
    write_csv(results/"FILA_32_AMBIGUIDADES_PARA_MT5.csv", queue[0].keys(), queue)
    result = {"estado": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "dd_por_prefixos_independentes": str(independent_dd),
              "limite": "Conferência do replay teórico; nenhuma resolução por ticks ou execução MT5 produzida."}
    (results/"VALIDACAO_EXATA_E_DD_INDEPENDENTE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("referencias", type=Path)
    parser.add_argument("resultados", type=Path)
    args = parser.parse_args()
    output = validate(args.referencias, args.resultados)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    raise SystemExit(0 if output["estado"] == "PASS" else 1)
