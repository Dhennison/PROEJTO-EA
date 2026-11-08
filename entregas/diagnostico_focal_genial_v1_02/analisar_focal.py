"""Recalcula OHLC dos CSVs brutos sem usar os deltas do relatório nativo.

python analisar_focal.py /pasta/F102_... --saida /pasta/analise
Não é necessário executar no notebook: o usuário pode enviar a pasta dos retornos.
"""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def number(text):
    value=Decimal(text)
    if not value.is_finite():raise ValueError("Campo não finito")
    return value


def stamp(text):
    return int((datetime.strptime(text,"%Y.%m.%d %H:%M:%S")-datetime(1970,1,1)).total_seconds()*1000)


def tick_stats(rows,lo,hi):
    selected=[r for r in rows if lo<=int(r["time_msc"])<hi and int(r["flags"]) & 120]
    if not selected:return None
    prices=[number(r["last"]) for r in selected]
    if min(prices)<=0:raise ValueError("Negócio sem Last positivo")
    return dict(zip(("O","H","L","C"),(prices[0],max(prices),min(prices),prices[-1])))


def validate_ticks(rows,n,lo,hi):
    if len(rows)!=n:raise ValueError("Quantidade de ticks difere do relatório")
    previous=lo
    for i,r in enumerate(rows):
        if int(r["indice"])!=i:raise ValueError("Índice de tick ausente/duplicado")
        time=int(r["time_msc"])
        if time<previous or not lo<=time<hi:raise ValueError("Tick fora da janela ou ordem")
        previous=time
        for field in ("bid","ask","last","volume_real"):number(r[field])
        if int(r["flags"]) & 120 and number(r["last"])<=0:raise ValueError("Last de negócio inválido")


def parse_report(path):
    return dict(line.split("=",1) for line in path.read_text(encoding="utf-8-sig").splitlines() if "=" in line)


def analyze(folder,out):
    trace=read(folder/"TENTATIVAS.csv")
    meta=parse_report(folder/"META.txt")
    completed=bool(trace and trace[-1]["fase"]=="END")
    details=[];windows=[]
    for idx in (1,2):
        base=f"JANELA{idx}"
        report=parse_report(folder/(base+"_RELATORIO.txt"))
        window={"janela":idx,"validade_declarada":report["Valido"],"estabilidade_declarada":report["Estavel"],"inicio":report["De"],"fim_exclusivo":report["AteExclusivo"]}
        windows.append(window)
        if report["Valido"]!="SIM":
            window["estado"]="INVALIDO_SEM_COMPARACAO";continue
        all_rows=read(folder/(base+"_ALL.csv"));trade=read(folder/(base+"_TRADE.csv"));rates=read(folder/(base+"_M1.csv"))
        lo,hi=stamp(report["De"]),stamp(report["AteExclusivo"])
        validate_ticks(all_rows,int(report["ALL_n"]),lo,hi);validate_ticks(trade,int(report["TRADE_n"]),lo,hi)
        if len(rates)!=int(report["M1_n"]):raise ValueError("Quantidade M1 difere do relatório")
        by_minute={int(r["time"])*1000:r for r in rates}
        if len(by_minute)!=len(rates):raise ValueError("M1 duplicado")
        if any(not lo<=k<hi or (k-lo)%60000 for k in by_minute):raise ValueError("M1 fora da janela/alinhamento")
        for row in rates:
            o,h,l,c=(number(row[key]) for key in ("open","high","low","close"))
            if not 0<l<=min(o,c)<=max(o,c)<=h:raise ValueError("M1 OHLC inválido")
        window["flags_ALL"]={str(k):v for k,v in sorted(Counter(int(r["flags"]) for r in all_rows).items())}
        window["ticks_all"]=len(all_rows);window["ticks_trade"]=len(trade)
        for minute in range(lo,hi,60000):
            a=tick_stats(all_rows,minute,minute+60000);b=tick_stats(trade,minute,minute+60000);bar=by_minute.get(minute)
            ref=None if bar is None else {field:number(bar[key]) for field,key in zip(("O","H","L","C"),("open","high","low","close"))}
            r={"Janela":idx,"MinutoServidor":(datetime(1970,1,1)+timedelta(milliseconds=minute)).isoformat(),"SnapshotEstavel":report["Estavel"]}
            for name,stats in (("ALL",a),("TRADE",b),("M1",ref)):
                for field in ("O","H","L","C"):r[f"{name}_{field}"]="" if stats is None else str(stats[field])
            for name,stats in (("ALL",a),("TRADE",b)):
                r[f"Campos_{name}_Diferentes_M1"]="SEM_M1" if ref is None else "SEM_NEGOCIO" if stats is None else "|".join(f for f in ref if stats[f]!=ref[f]) or "IGUAL"
                for field in ("O","H","L","C"):r[f"Delta_{name}_{field}"]="" if ref is None or stats is None else str(stats[field]-ref[field])
            details.append(r)
        window["estado"]="ESTAVEL_PARA_ANALISE" if report["Estavel"]=="SIM" else "PROVISORIO_NAO_ESTAVEL"
    out.mkdir(parents=True,exist_ok=True)
    if details:
        with (out/"OHLC_RECALCULADO.csv").open("w",encoding="utf-8-sig",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=details[0].keys(),delimiter=";",lineterminator="\n");writer.writeheader();writer.writerows(details)
    result={"lote_tem_marcador_END":completed,"metadados":meta,"janelas":windows,
            "limite":"Recalcula o snapshot exportado, não prova causa da diferença, integridade de toda a sessão, identificação histórica ou execução no Tester. Modo Bid não permite interpretar diferença Last/M1 como erro da base de negócios."}
    (out/"RESUMO.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("pasta",type=Path);parser.add_argument("--saida",type=Path,required=True);args=parser.parse_args()
    print(json.dumps(analyze(args.pasta,args.saida),ensure_ascii=False,indent=2))
