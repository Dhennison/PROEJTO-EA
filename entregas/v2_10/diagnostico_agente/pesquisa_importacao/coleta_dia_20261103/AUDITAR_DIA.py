"""Audita o CSV integral dentro do ZIP sem extrair/alterar entradas.

Compara negocios Last/flags com as barras M1 originais e a amostra conhecida.
Nao preenche campos esparsos, nao remove zeros e nao deduplica negocios.
Nao reproduz validacao do motor MT5. Processamento em streaming.
"""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
ZIP = ROOT / "WINZ26_20261030_DIA_COMPLETO.zip"
M1 = ROOT.parents[2] / "validacao_20261102_ensaio1/WINZ26_M1_202610300900_202610301824.csv"
SAMPLE = ROOT.parent / "DADOS_ORIGINAIS/WINZ26_202610300900_202610300901.csv"
EXPECTED_HEADER = ["<DATE>", "<TIME>", "<BID>", "<ASK>", "<LAST>", "<VOLUME>", "<FLAGS>"]


def new_minute():
    return {"rows": 0, "trade_rows": 0, "volume": Decimal(0), "open": None,
            "high": None, "low": None, "close": None, "flags_zero": 0, "all_zero": 0,
            "first_time": None, "last_time": None, "last_outside_m1_range": 0}


def add_trade(item, price, volume):
    if item["trade_rows"] == 0:
        item["open"] = item["high"] = item["low"] = price
    item["trade_rows"] += 1
    item["close"] = price
    item["high"] = max(item["high"], price)
    item["low"] = min(item["low"], price)
    item["volume"] += volume


def main():
    with M1.open(encoding="utf-8-sig", newline="") as stream:
        bars = {row["<TIME>"][:5]: row for row in csv.DictReader(stream, delimiter="\t")}
    minutes, flags = {}, Counter()
    digest, sample_digest = hashlib.sha256(), hashlib.sha256()
    rows = sample_rows = regressions = duplicate_timestamps = consecutive_identical_rows = 0
    off_grid = Counter()
    previous = previous_raw = None
    first = last = None
    zero_samples = []
    daily = new_minute()
    negative_volume_rows = positive_trade_zero_volume_rows = last_without_trade_flags = 0
    zip_hash = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    with zipfile.ZipFile(ZIP) as archive:
        candidates = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(candidates) != 1 or not candidates[0].filename.lower().endswith(".csv"):
            raise ValueError("Expected one CSV in archive")
        entry = candidates[0]
        with archive.open(entry) as stream:
            header = stream.readline()
            if header.decode("utf-8-sig").rstrip("\r\n").split("\t") != EXPECTED_HEADER:
                raise ValueError("Unexpected tick header")
            digest.update(header)
            sample_digest.update(header)
            for csv_line, raw in enumerate(stream, start=2):
                digest.update(raw)
                cells = raw.decode("utf-8").rstrip("\r\n").split("\t")
                if len(cells) != 7:
                    raise ValueError(f"Unexpected field count at CSV line{csv_line}")
                date, time, bid, ask, last_price, volume_text, flag_text = cells
                if date != "2026.10.30" or len(time) != 12 or time[2] != ":" or time[5] != ":" or time[8] != ".":
                    raise ValueError(f"Unexpected timestamp at CSV line{csv_line}")
                if not (0 <= int(time[:2]) < 24 and 0 <= int(time[3:5]) < 60 and
                        0 <= int(time[6:8]) < 60 and 0 <= int(time[9:]) < 1000):
                    raise ValueError(f"Invalid timestamp at CSV line{csv_line}")
                timestamp = date + " " + time
                rows += 1
                if first is None:
                    first = timestamp
                last = timestamp
                if previous is not None:
                    regressions += timestamp < previous
                    duplicate_timestamps += timestamp == previous
                    consecutive_identical_rows += raw == previous_raw
                previous, previous_raw = timestamp, raw
                flags_value = int(flag_text)
                flags[flags_value] += 1
                price_values = [int(value) if value else 0 for value in (bid, ask, last_price)]
                for field, value in zip(("BID", "ASK", "LAST"), price_values):
                    if value > 0 and value % 5:
                        off_grid[field] += 1
                price = price_values[2]
                if price > 0 and not (flags_value & 120):
                    last_without_trade_flags += 1
                minute = time[:5]
                item = minutes.setdefault(minute, new_minute())
                item["rows"] += 1
                item["first_time"] = item["first_time"] or time
                item["last_time"] = time
                if flags_value == 0:
                    item["flags_zero"] += 1
                    explicit_zero = all(value != "" and Decimal(value) == 0 for value in cells[2:])
                    item["all_zero"] += explicit_zero
                    if len(zero_samples) < 20:
                        zero_samples.append({"csv_line": csv_line, "fields": cells, "explicit_all_zero": explicit_zero})
                if flags_value & 120 and price > 0:
                    volume = Decimal(volume_text or "0")
                    if not volume.is_finite():
                        raise ValueError(f"Nonfinite volume at CSV line{csv_line}")
                    negative_volume_rows += volume < 0
                    positive_trade_zero_volume_rows += volume == 0
                    add_trade(item, price, volume)
                    add_trade(daily, price, volume)
                    if minute in bars:
                        bar = bars[minute]
                        item["last_outside_m1_range"] += price < int(bar["<LOW>"]) or price > int(bar["<HIGH>"])
                if "09:00:00.000" <= time <= "09:01:00.000":
                    sample_digest.update(raw)
                    sample_rows += 1
                if rows % 1_000_000 == 0:
                    print(f"AUDIT_PROGRESS;rows={rows}", flush=True)
    minute_rows = []
    mismatches = []
    for minute, item in sorted(minutes.items()):
        record = {"minute": minute, **item}
        record["volume"] = str(record["volume"])
        record["has_original_m1"] = minute in bars
        if minute in bars:
            bar = bars[minute]
            checks = {name: item[name.lower()] == int(bar["<" + name + ">"])
                      for name in ("OPEN", "HIGH", "LOW", "CLOSE")}
            checks["VOL"] = item["volume"] == Decimal(bar["<VOL>"])
            record["original_m1"] = bar
            record["comparison"] = checks
            if not all(checks.values()):
                mismatches.append({"minute": minute, "checks": checks})
        minute_rows.append(record)
    result = {
        "zip_file": ZIP.name, "zip_bytes": ZIP.stat().st_size, "zip_sha256": zip_hash,
        "csv_member": entry.filename, "csv_bytes": entry.file_size, "csv_sha256": digest.hexdigest(),
        "zip_crc_check": "passed_by_reading_member_to_eof",
        "rows": rows, "ui_received_rows": 4319285, "matches_ui_count": rows == 4319285,
        "first_time": first, "last_time": last, "timestamp_regressions": regressions,
        "same_timestamp_consecutive_pairs": duplicate_timestamps,
        "identical_consecutive_row_pairs_preserved": consecutive_identical_rows,
        "flag_counts": dict(sorted(flags.items())), "off_tick_size5_counts": dict(off_grid),
        "negative_trade_volume_rows": negative_volume_rows,
        "positive_trade_zero_volume_rows": positive_trade_zero_volume_rows,
        "positive_last_without_trade_flags": last_without_trade_flags,
        "explicit_all_zero_rows": sum(item["all_zero"] for item in minutes.values()),
        "zero_flag_samples": zero_samples,
        "positive_trade_rows": daily["trade_rows"], "trade_volume": str(daily["volume"]),
        "trade_ohlc": [daily[name] for name in ("open", "high", "low", "close")],
        "original_minute_sample_rows": sample_rows, "original_minute_sample_sha256": sample_digest.hexdigest(),
        "minute_sample_byte_identical": sample_digest.hexdigest() == hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
        "original_m1_rows": len(bars), "minutes_with_tick_rows": len(minutes),
        "m1_minutes_without_tick_rows": sorted(set(bars) - set(minutes)),
        "tick_minutes_without_original_m1": sorted(set(minutes) - set(bars)),
        "ohlc_volume_mismatching_minutes": mismatches,
        "all_trade_ohlc_volume_match_available_m1": not mismatches and not (set(bars) - set(minutes)),
        "minutes": minute_rows,
        "scope": "Offline comparison of user-provided CSV and older M1 export; not native Tester validation",
    }
    (ROOT / "AUDITORIA_DIA.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    with (ROOT / "COMPARACAO_POR_MINUTO.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["minute", "rows", "trade_rows", "volume", "open", "high", "low", "close",
                         "flags_zero", "all_zero", "has_original_m1", "OHLC_VOL_equal"])
        for item in minute_rows:
            writer.writerow([item[name] for name in ("minute", "rows", "trade_rows", "volume", "open", "high", "low", "close",
                                                    "flags_zero", "all_zero", "has_original_m1")] +
                            [all(item["comparison"].values()) if "comparison" in item else "not_comparable"])
    brief = {key: value for key, value in result.items() if key not in ("minutes", "zero_flag_samples")}
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
