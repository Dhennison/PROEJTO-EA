"""Confere M1 atual e calcula fingerprint de eventos sinalizados do CSV original.

O fingerprint e um controle de integridade de 64 bits, nao hash criptografico.
Nao modifica o CSV nem remove suas linhas zeradas. Elas sao contabilizadas,
mas nao sao eventos sinalizados para fins dessa comparacao com a API nativa.
"""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
M1 = ROOT / "WINZ26_M1_20261030_SECUNDARIO_ATUAL.csv"
OLD = ROOT.parents[2] / "validacao_20261102_ensaio1/WINZ26_M1_202610300900_202610301824.csv"
ZIP = BASE / "coleta_dia_20261103/WINZ26_20261030_DIA_COMPLETO.zip"
SEED = 14695981039346656037
PRIME = 1099511628211
MASK = (1 << 64) - 1


def mix(state, values):
    for value in values:
        state = ((state ^ value) * PRIME) & MASK
    return state


def signed(value):
    return value if value < (1 << 63) else value - (1 << 64)


def main():
    with M1.open(newline="") as stream:
        bars = list(csv.DictReader(stream, delimiter="\t"))
    current = {bar["<TIME>"][:5]: bar for bar in bars}
    audit = json.loads((BASE / "coleta_dia_20261103/AUDITORIA_DIA.json").read_text())
    comparisons = []
    for minute in audit["minutes"]:
        name = minute["minute"]
        if name not in current:
            continue
        bar = current[name]
        same = {key: minute[key.lower()] == int(bar["<" + key + ">"])
                for key in ("OPEN", "HIGH", "LOW", "CLOSE")}
        same["VOL"] = Decimal(minute["volume"]) == Decimal(bar["<VOL>"])
        comparisons.append({"minute": name, "equal": all(same.values()), "fields_equal": same,
                            "ticks": {key: minute[key] for key in ("open", "high", "low", "close", "volume")}, "M1": bar})
    h_all = h_trade = SEED
    all_count = trade_count = zero_count = volume_sum = 0
    last_msc = first_msc = None
    with zipfile.ZipFile(ZIP) as archive:
        with archive.open(audit["csv_member"]) as raw:
            for index, row in enumerate(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t"), start=1):
                flags = int(row["<FLAGS>"])
                if flags == 0:
                    zero_count += 1
                    continue
                t = row["<TIME>"]
                msc = 1793318400000 + int(t[:2]) * 3600000 + int(t[3:5]) * 60000 + int(t[6:8]) * 1000 + int(t[9:])
                prices = [int(row[key]) if flags & bit else 0
                          for key, bit in (("<BID>", 2), ("<ASK>", 4), ("<LAST>", 8))]
                volume = Decimal(row["<VOLUME>"]) if flags & 16 else Decimal(0)
                if volume != volume.to_integral_value() or volume < 0:
                    raise ValueError("Expected integral nonnegative contract volume")
                values = (msc, flags, *prices, int(volume))
                h_all = mix(h_all, values)
                all_count += 1
                first_msc = first_msc if first_msc is not None else msc
                last_msc = msc
                if flags & 120 and Decimal(row["<LAST>"] or "0") > 0:
                    h_trade = mix(h_trade, values)
                    trade_count += 1
                    volume_sum += int(volume)
                if index % 1000000 == 0:
                    print(f"CANONICAL_PROGRESS;rows={index}", flush=True)
    assert all_count + zero_count == audit["rows"]
    assert trade_count == audit["positive_trade_rows"]
    assert volume_sum == Decimal(audit["trade_volume"])
    result = {
        "current_m1_file": M1.name, "current_m1_sha256": hashlib.sha256(M1.read_bytes()).hexdigest(),
        "current_m1_rows": len(bars), "byte_identical_to_older_m1": M1.read_bytes() == OLD.read_bytes(),
        "matching_minutes": sum(item["equal"] for item in comparisons),
        "differences": [item for item in comparisons if not item["equal"]],
        "dataset_zip_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest(),
        "source_csv_sha256": audit["csv_sha256"], "source_rows": audit["rows"],
        "source_zero_flag_rows": zero_count, "signaled_event_rows": all_count,
        "positive_trade_rows": trade_count, "positive_trade_volume": volume_sum,
        "first_signaled_msc": first_msc, "last_signaled_msc": last_msc,
        "fingerprint_method": "start14695981039346656037; each of 6 unsigned integers: (state XOR value)*1099511628211 modulo2^64",
        "fingerprint_fields": "time_msc,flags,BID if flags2 else0,ASK if flags4 else0,LAST if flags8 else0,VOLUME if flags16 else0",
        "fingerprint_all_hex": f"{h_all:016X}", "fingerprint_all_signed": signed(h_all),
        "fingerprint_trade_hex": f"{h_trade:016X}", "fingerprint_trade_signed": signed(h_trade),
        "scope": "Flag-directed canonical events; ignores carried values in unflagged fields, not raw MqlTick byte equality or cryptographic proof",
    }
    (ROOT / "M1_E_SEQUENCIA.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "differences"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
