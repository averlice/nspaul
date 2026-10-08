"""Trim silence, QC, and build metadata for the VW Paul dataset.

Reads prompts.tsv + wavs/, writes trimmed wavs to wavs_trimmed/,
then drops clips (from the shuffled tail) until total size <= SIZE_BUDGET_MB,
and emits metadata.csv / metadata.jsonl for the final kept set.
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(r"C:\paul")
WAVS = ROOT / "wavs"
OUT = ROOT / "wavs_trimmed"
PROMPTS = ROOT / "prompts.tsv"
PAD = 0.1          # seconds of padding kept at each end
THRESH_DB = -40.0  # silence threshold
SIZE_BUDGET_MB = 780.0
MIN_DUR, MAX_DUR = 0.8, 15.0
MIN_PEAK = 0.01    # reject near-silent clips

def load_prompts():
    prompts = {}
    with open(PROMPTS, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            pid, text = line.split("\t", 1)
            prompts[pid] = text
    return prompts

def main():
    prompts = load_prompts()
    OUT.mkdir(exist_ok=True)

    stats = []
    dropped_qc = []
    for i, (pid, text) in enumerate(sorted(prompts.items())):
        src = WAVS / f"{pid}.wav"
        if not src.exists():
            dropped_qc.append((pid, "missing"))
            continue
        data, sr = sf.read(src, dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        # trim by amplitude envelope
        amp = np.abs(data)
        thr = 10 ** (THRESH_DB / 20)
        voiced = np.where(amp > thr)[0]
        if voiced.size == 0:
            dropped_qc.append((pid, "silence"))
            continue
        pad = int(PAD * sr)
        a = max(0, int(voiced[0]) - pad)
        b = min(len(data), int(voiced[-1]) + pad + 1)
        clip = data[a:b]
        dur = len(clip) / sr
        if dur < MIN_DUR or dur > MAX_DUR:
            dropped_qc.append((pid, f"dur={dur:.2f}"))
            continue
        if float(np.max(np.abs(clip))) < MIN_PEAK:
            dropped_qc.append((pid, "low_peak"))
            continue
        sf.write(OUT / f"{pid}.wav", clip, sr, subtype="PCM_16")
        stats.append({
            "id": pid,
            "text": text,
            "duration": round(dur, 3),
            "bytes": int(len(clip) * 2),
        })
        if (i + 1) % 1000 == 0:
            print(f"  processed {i+1}/{len(prompts)}", flush=True)

    # order: keep original shuffled id order, trim from tail to fit budget
    stats.sort(key=lambda r: r["id"])
    budget = int(SIZE_BUDGET_MB * 1024 * 1024)
    total = sum(r["bytes"] for r in stats)
    print(f"after trim+QC: {len(stats)} clips, {total/1024/1024:.0f} MB "
          f"(budget {SIZE_BUDGET_MB:.0f} MB)", flush=True)

    dropped_budget = []
    while stats and sum(r["bytes"] for r in stats) > budget:
        r = stats.pop()
        dropped_budget.append(r["id"])

    kept_total = sum(r["bytes"] for r in stats)
    kept_dur = sum(r["duration"] for r in stats)
    print(f"kept: {len(stats)} clips, {kept_total/1024/1024:.0f} MB, "
          f"{kept_dur/3600:.2f} h; dropped_budget={len(dropped_budget)}, "
          f"dropped_qc={len(dropped_qc)}", flush=True)

    # delete trimmed files for dropped clips
    for pid in dropped_budget:
        (OUT / f"{pid}.wav").unlink(missing_ok=True)

    with open(ROOT / "metadata.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "audio_file", "text", "duration"])
        for r in stats:
            w.writerow([r["id"], f"wavs/{r['id']}.wav", r["text"], r["duration"]])

    with open(ROOT / "metadata.jsonl", "w", encoding="utf-8") as f:
        for r in stats:
            f.write(json.dumps({
                "audio_file": f"wavs/{r['id']}.wav",
                "text": r["text"],
                "duration": r["duration"],
            }, ensure_ascii=False) + "\n")

    with open(ROOT / "qc_report.txt", "w", encoding="utf-8") as f:
        for pid, why in dropped_qc:
            f.write(f"{pid}\t{why}\n")
        for pid in dropped_budget:
            f.write(f"{pid}\tbudget\n")

    # stats for STATS.md
    durs = sorted(r["duration"] for r in stats)
    n = len(durs)
    with open(ROOT / "stats.json", "w", encoding="utf-8") as f:
        json.dump({
            "clips": n,
            "hours": round(kept_dur / 3600, 2),
            "size_mb": round(kept_total / 1024 / 1024, 1),
            "sample_rate": 22050,
            "duration_min": durs[0],
            "duration_median": durs[n // 2],
            "duration_max": durs[-1],
            "dropped_qc": len(dropped_qc),
            "dropped_budget": len(dropped_budget),
        }, f, indent=2)

if __name__ == "__main__":
    main()
