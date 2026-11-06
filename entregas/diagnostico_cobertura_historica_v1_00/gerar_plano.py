"""Gera consultas candidatas em lote; calendário NÃO identifica contrato histórico."""
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "historico_work_modelo_d_20261105"
MONTHS = {2: "G", 4: "J", 6: "M", 8: "Q", 10: "V", 12: "Z"}
FIELDS = "Data;Anterior;FimExclusivo;CorteWork;AjusteWork;Candidato1;Candidato2;ContratoConfirmado;EvidenciaContrato;AjusteB3;EvidenciaB3;FusoBRTConfirmado;AberturaWork;HighAnteriorWork;LowAnteriorWork;CloseAnteriorWork;FonteWork;BarrasWork;PrimeiraBarraWork".split(";")


def candidates(day):
    options = []
    for year in (day.year, day.year+1):
        for month, code in MONTHS.items():
            middle = date(year, month, 15)
            nominal = middle+timedelta(days=(2-middle.weekday()+3) % 7-3)
            # Regra nominal, sem certificar calendário de feriados ou rolagem por liquidez.
            if nominal >= day:
                options.append((f"WIN{code}{year % 100:02d}", nominal))
    return options[:2]


def generate():
    path = BASE / "replay_completo_20261106/resultados/CONTEXTO_E_4385_NIVEIS.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        contexts = list(csv.DictReader(stream, delimiter=";"))
    rows = []
    for r in contexts:
        day = date.fromisoformat(r["Data"])
        first, second = candidates(day)
        step = 1 if "1min" in r["ArquivoAtual"] else 5
        ending = (datetime.fromisoformat(r["Data"]+" "+r["UltimaBarra"])+timedelta(minutes=step)).time().isoformat()
        rows.append(dict(zip(FIELDS, (day.strftime("%Y.%m.%d"), date.fromisoformat(r["PregaoAnterior"]).strftime("%Y.%m.%d"),
                                     ending, r["Corte"], r["Ajuste"], first[0], second[0], "", "", "", "", "NAO",
                                     r["Abertura"], r["MaximaAnterior"], r["MinimaAnterior"], r["FechamentoAnterior"],
                                     r["ArquivoAtual"], r["Barras"], r["PrimeiraBarra"]))))
    if len(rows) != 877 or len({r["Data"] for r in rows}) != 877:
        raise ValueError("Universo deve conter 877 datas únicas")
    out = ROOT / "MQL5/Files/PLANO_HC100_877.csv"
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter=";", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    return rows


if __name__ == "__main__":
    print("Plano gerado:", len(generate()), "pregões; vínculos históricos em branco.")
