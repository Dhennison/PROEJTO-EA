"""Lê DIAS.csv, verifica checksum e considera a última rodada concluída por tarefa.

Uso: python resumir_relatorios.py /pasta/dos/retornos --saida resumo
O usuário pode simplesmente enviar os retornos; Python não é necessário no MT5.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def checksum(text):
    encoded = text.encode("utf-16-le", errors="surrogatepass")
    value = 1469598103934665603
    for i in range(0, len(encoded), 2):
        value = ((value ^ int.from_bytes(encoded[i:i+2], "little"))*1099511628211) & ((1 << 64)-1)
    return str(value)


def load(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines:
        raise ValueError(f"Relatório vazio: {path}")
    header = lines[0].split(";")
    if len(header) != 35 or header[-1] != "Checksum":
        raise ValueError(f"Cabeçalho inválido: {path}")
    latest = {}
    for position, line in enumerate(lines[1:], 2):
        if not line:
            continue
        cells = line.split(";")
        if len(cells) != len(header) or checksum(";".join(cells[:-1])) != cells[-1]:
            raise ValueError(f"Linha incompleta/checksum inválido: {path}:{position}")
        row = dict(zip(header, cells))
        task = int(row["Task"])
        if task in latest and (latest[task]["Data"], latest[task]["SimboloConsultado"]) != (row["Data"], row["SimboloConsultado"]):
            raise ValueError("Identidade da tarefa mudou")
        latest[task] = row
    return list(latest.values())


def summarize(paths):
    rows = []
    for path in paths:
        rows.extend({"Arquivo": path.name, **row} for row in load(path))
    return {"arquivos_relatorios": len(paths), "tarefas_concluidas": len(rows),
            "datas_simbolos_distintos": len({(r["Data"], r["SimboloConsultado"]) for r in rows}),
            "por_estado_ticks": dict(Counter(r["TicksEstado"] for r in rows)),
            "candidatos_tecnicos_sem_vinculos": sum(r["CandidatoTecnicoSemVinculos"] == "SIM_SUJEITO_A_VINCULOS" for r in rows),
            "candidatos_a_piloto_conforme_declaracoes": sum(r["DadosPrimeiroPiloto"] != "PENDENTE" for r in rows),
            "limite": "Resume somente tarefas concluídas. Metadados atuais não identificam contrato histórico e os vínculos declarados exigem revisão documental."}, rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.pasta.glob("*_DIAS.csv"))
    if not files:
        raise SystemExit("Nenhum *_DIAS.csv encontrado")
    summary, rows = summarize(files)
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida/"RESUMO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    if rows:
        with (args.saida/"ULTIMAS_RODADAS.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter=";", lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
