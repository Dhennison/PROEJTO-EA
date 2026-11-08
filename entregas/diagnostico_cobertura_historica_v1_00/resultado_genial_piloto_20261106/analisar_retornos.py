"""Cruza os retornos nativos; não consulta servidor e não aprova dados do Tester."""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent
sys.path.insert(0, str(DIAG))
from resumir_relatorios import checksum, load


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def write(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter=";", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def ms_datetime(value):
    # Mesma representação numérica dos pedidos no relatório; sem deslocar para
    # timezone do PC. A certificação do fuso histórico é outra verificação.
    return datetime(1970, 1, 1)+timedelta(milliseconds=int(value))


def analyze():
    inputs = HERE/"arquivos_recebidos"
    days = load(next(inputs.glob("*_DIAS.csv")))  # valida checksums e rodadas finais
    blocks = read(next(inputs.glob("*_BLOCOS.csv")))
    meta = dict(line.split("=", 1) for line in next(inputs.glob("*_META.txt")).read_text(encoding="utf-8-sig").splitlines() if "=" in line)
    plan_text = (DIAG/"MQL5/Files/PLANO_HC100_877.csv").read_text(encoding="utf-8-sig")
    assert checksum("\n".join(x.strip() for x in plan_text.splitlines() if x.strip())) == meta["PlanoHash"]
    assert meta["Ambiente"] == "TERMINAL" and meta["Servidor"] == "GenialInvestimentos-PRD"
    reference = {r["Data"]: r for r in read(DIAG/"REFERENCIA_CONFERIDA_SETEMBRO/CONTEXTO_14_PREGOES.csv")}
    plans = {r["Data"]: r for r in read(DIAG/"MQL5/Files/PLANO_HC100_877.csv")}
    assert len(days) == 14 and {r["Data"].replace(".", "-") for r in days} == set(reference)
    accepted, orphan, daily, pending = [], [], [], []
    pre_ok = pre_bad = post_ok = post_bad = 0
    for b in blocks:
        matching = [r for r in days if (r["Task"], r["Rodada"], r["Data"], r["SimboloConsultado"]) == (b["Task"], b["Rodada"], b["Data"], b["Simbolo"])]
        (accepted if matching else orphan).append(b)
    keys = {(r["Task"], r["Rodada"], r["DeMsc"], r["AteExclusivoMsc"]) for r in accepted}
    assert len(keys) == len(accepted)
    for row in days:
        day = row["Data"]; ref = reference[day.replace(".", "-")]; plan = plans[day]
        for a, b in (("AjusteWork", "Ajuste"), ("HighAnteriorContrato", "MaximaAnterior"),
                     ("LowAnteriorContrato", "MinimaAnterior"), ("CloseAnteriorContrato", "FechamentoAnterior"), ("OpenTicksContrato", "Abertura")):
            assert D(row[a]) == D(ref[b]), (day, a)
        subset = sorted((b for b in accepted if b["Task"] == row["Task"]), key=lambda b: int(b["DeMsc"]))
        assert len(subset) == int(row["Janelas"])
        assert sum(b["Estado"] == "CONFERIDO" for b in subset) == int(row["JanelasConferidas"])
        assert sum(b["Estado"] == "PENDENTE" for b in subset) == int(row["JanelasPendentes"])
        good = [b for b in subset if b["Estado"] == "CONFERIDO"]
        assert sum(int(b["ALL_n"]) for b in good) == int(row["TicksALLValidosEstaveis"])
        assert sum(int(b["Negocios"]) for b in good) == int(row["NegociosValidosEstaveis"])
        assert ms_datetime(subset[0]["DeMsc"]).strftime("%Y.%m.%d %H:%M:%S") == day+" 09:00:00"
        assert ms_datetime(subset[-1]["AteExclusivoMsc"]).strftime("%H:%M:%S") == plan["FimExclusivo"]
        assert all(a["AteExclusivoMsc"] == b["DeMsc"] for a, b in zip(subset, subset[1:]))
        cutoff = datetime.fromisoformat(day.replace(".", "-")+" "+plan["CorteWork"])
        pre = [b for b in subset if ms_datetime(b["AteExclusivoMsc"]) <= cutoff]
        post = [b for b in subset if ms_datetime(b["DeMsc"]) >= cutoff]
        assert len(pre)+len(post) == len(subset)
        bad_pre = [b for b in pre if b["Estado"] == "PENDENTE"]
        bad_post = [b for b in post if b["Estado"] == "PENDENTE"]
        pre_ok += len(pre)-len(bad_pre); pre_bad += len(bad_pre)
        post_ok += len(post)-len(bad_post); post_bad += len(bad_post)
        intervals = []
        for b in bad_pre+bad_post:
            start = ms_datetime(b["DeMsc"]); end = ms_datetime(b["AteExclusivoMsc"])
            intervals.append(start.strftime("%H:%M")+"-"+end.strftime("%H:%M"))
            pending.append({"Data": day, "SimboloConsultado": b["Simbolo"], "InicioServidor": start.isoformat(), "FimExclusivoServidor": end.isoformat(),
                            "RelacaoComCorte": "ANTES_18H" if b in bad_pre else "APOS_CORTE",
                            "TicksALLNaLeituraFinal": b["ALL_n"], "NegociosNaLeituraFinal": b["Negocios"],
                            "Leituras": b["Leituras"], "ErroTicksUltimaLeitura": b["ErroTicks"], "ErroM1UltimaLeitura": b["ErroM1"], "Motivo": b["Motivo"],
                            "Limite": "CSV v1.00 não guarda minuto ou O/H/L/C divergentes; requer consulta focalizada."})
        daily.append({"Data": day, "SimboloConsultado": row["SimboloConsultado"], "Janelas": len(subset), "Conferidas": len(good),
                      "PendentesAntes18h": len(bad_pre), "PendentesDepoisCorte": len(bad_post), "MinutosOHLCDiferente": row["MinutosDiferentes"],
                      "NegociosNasJanelasConferidas": row["NegociosValidosEstaveis"], "HLCAnteriorWork": "IGUAL", "AberturaWork": "IGUAL", "AjusteWorkPlano": "IGUAL",
                      "JanelasPendentes": " | ".join(intervals),
                      "CandidatoTecnicoRecorteAte18h": "SIM_COM_RESSALVAS" if not bad_pre else "PENDENTE_DIVERGENCIAS_INTRADIA",
                      "IdentificacaoHistoricaContrato": row["ContratoHistorico"], "VinculoAjusteB3": row["AjusteVinculo"], "FusoHistorico": "NAO_CERTIFICADO", "EntregaNoTester": "NAO_TESTADA"})
    out = HERE/"analise_completa"; out.mkdir(exist_ok=True)
    write(out/"CONFERENCIA_POR_PREGAO.csv", daily)
    write(out/"JANELAS_PENDENTES_PARA_CONSULTA_FOCAL.csv", pending)
    all_n = sum(int(b["ALL_n"]) for b in accepted)
    trades = sum(int(b["Negocios"]) for b in accepted)
    good_n = sum(int(r["TicksALLValidosEstaveis"]) for r in days)
    good_trades = sum(int(r["NegociosValidosEstaveis"]) for r in days)
    summary = {"servidor": meta["Servidor"], "ambiente": meta["Ambiente"], "plano_hash_confere": True, "checksums_14_linhas_diarias": "PASS",
               "pregoes": len(days), "janelas": len(accepted), "janelas_de_rodadas_nao_concluidas": len(orphan),
               "janelas_conferidas": sum(r["Estado"] == "CONFERIDO" for r in accepted), "janelas_pendentes": len(pending),
               "percentual_janelas_conferidas": str(D(sum(r["Estado"] == "CONFERIDO" for r in accepted))/D(len(accepted))*100),
               "antes_corte": {"conferidas": pre_ok, "pendentes": pre_bad},
               "apos_corte": {"conferidas": post_ok, "pendentes": post_bad},
               "datas_sem_pendencia_antes_corte": [r["Data"] for r in daily if r["PendentesAntes18h"] == 0],
               "datas_com_pendencia_antes_corte": [r["Data"] for r in daily if r["PendentesAntes18h"] > 0],
               "minutos_sem_ticks_com_m1": sum(int(r["MinutosSemTicksComM1"]) for r in days),
               "minutos_sem_m1_com_ticks": sum(int(r["MinutosSemM1ComTicks"]) for r in days),
               "minutos_com_ohlc_diferente": sum(int(r["MinutosDiferentes"]) for r in days),
               "negocios_janelas_conferidas": good_trades, "all_janelas_conferidas": good_n,
               "negocios_finais_janelas_pendentes": trades-good_trades, "all_finais_janelas_pendentes": all_n-good_n,
               "negocios_soma_leituras_finais_todos_blocos": trades, "all_soma_leituras_finais_todos_blocos": all_n,
               "erros_registrados_leitura_final_ticks": dict(Counter(r["ErroTicks"] for r in accepted)),
               "erros_registrados_leitura_final_m1": dict(Counter(r["ErroM1"] for r in accepted)),
               "distribuicao_leituras": dict(Counter(r["Leituras"] for r in accepted)),
               "contextos_aberturas_ajustes_work_iguais": len(daily),
               "offset_trade_server_gmt_apenas_no_inicio_segundos": int((datetime.fromisoformat(meta["TimeTradeServer"].replace(".", "-"))-datetime.fromisoformat(meta["TimeGMT"].replace(".", "-"))).total_seconds()),
               "limites": ["Consulta no terminal, não teste de entrega de dados no Tester.", "WINV26 é corroborado por dados, sem prova documental histórica de série/rolagem nesta coleta.",
                          "AjusteWork confere, mas vínculo com boletim B3 permanece pendente.", "Divergências em 18:20-18:25 são posteriores ao corte, mas não devem ser apagadas: podem afetar contexto ou validação do Tester.",
                          "Não há OHLC/minuto específico nos CSVs v1.00 para diagnosticar a causa dos 24 minutos divergentes.", "Zeros de erro são das leituras finais registradas, não de todas as chamadas de sincronização anteriores.", "Concordância entre ticks e M1 não certifica integridade total dos registros."]}
    (out/"RESUMO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(analyze(), ensure_ascii=False, indent=2))
