import json
import glob
import numpy as np
import soundfile as sf

stats = json.load(open("C:/paul/stats.json"))
durs = np.array([sf.info(f).duration for f in glob.glob("C:/paul/wavs/*.wav")])
hist, edges = np.histogram(durs, bins=[0, 1, 2, 3, 4, 6, 8, 10, 15])
lines = [
    "# Dataset statistics",
    "",
    f"- Clips: **{stats['clips']}**",
    f"- Total duration: **{stats['hours']} h** ({durs.sum():.0f} s)",
    f"- Size on disk: **{stats['size_mb']} MB**",
    f"- Format: **{stats['sample_rate']} Hz**, mono, 16-bit PCM WAV",
    f"- Duration: min {durs.min():.2f} s / median {np.median(durs):.2f} s / max {durs.max():.2f} s / mean {durs.mean():.2f} s",
    f"- QC: {stats['dropped_qc']} clips rejected (silence/peak/duration), {stats['dropped_budget']} dropped for size budget",
    "- Source prompts: 7000 sampled from 146587 unique sentences across 73 Gutenberg books",
    "",
    "## Duration distribution",
    "",
    "| range (s) | clips |",
    "|---|---|",
]
for h, a, b in zip(hist, edges[:-1], edges[1:]):
    lines.append(f"| {a:g}-{b:g} | {h} |")
lines += [
    "",
    "## Synthesis",
    "",
    "- Voice: VW Paul (SAPI5, Voiceware), 32-bit engine",
    "- Rate -2, volume 100 (engine defaults)",
    "- Sharded synthesis: 4 x 1750 clips, 0 failures, 0 retries",
    "",
]
open("C:/paul/STATS.md", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
