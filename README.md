# VW Paul — Piper fine-tuning dataset

A public-domain text, single-speaker speech dataset synthesized from the
**VW Paul** SAPI5 voice (Voiceware, 16 kHz-class engine), packaged for
training [Piper](https://github.com/rhasspy/piper) TTS voices.

## Contents

| Path | Description |
|------|-------------|
| `wavs/` | 3697 mono 16-bit PCM WAV clips @ 22050 Hz |
| `metadata.csv` | `id,audio_file,text,duration` (CSV) |
| `metadata.jsonl` | same records as JSON lines (`audio_file`, `text`, `duration`) |
| `scripts/` | the exact pipeline that produced this dataset |
| `LICENSE` | Unlicense (public domain dedication) — applies to the dataset |

## Dataset statistics

See [STATS.md](STATS.md).

- **3697 clips · 5.15 hours · 780 MB**
- 22050 Hz, mono, 16-bit PCM
- duration: 0.8 s – 14.6 s (median 4.6 s)

## Text provenance

Sentences come from 73 pre-1929 Project Gutenberg books (public domain in
the US), reflowed and sentence-split, then filtered:

- 10–28 words, at least two words per sentence
- ASCII-only; letters, space, and `, ' - ! ?` (final punctuation required)
- digits written out as words (`1998` → `nineteen ninety eight`);
  `Mr.`, `Mrs.`, `Dr.`, `St.`, `Prof.`, `etc.`, `vs.`, `U.S.`, `A.M.`/`P.M.`
  expanded before the filter
- the word `dataset` never appears (the voice pronounces it incorrectly);
  prompts use `data set` instead
- duplicates removed, then 7000 sentences sampled with a fixed seed

## Audio provenance

- Synthesized in-process with the 32-bit SAPI engine
  (`vtengsapi50.dll` from the VW Paul voice pack) via `SAPI.SpVoice` /
  `SAPI.SpFileStream` in 32-bit Windows PowerShell
- voice token: `HKLM\SOFTWARE\WOW6432Node\Microsoft\Speech\Voices\Tokens\VW Paul`
- rate/volume left at engine defaults (rate −2, volume 100)
- each clip trimmed to its voiced region with ~0.1 s padding
  (the engine output is already tight: 0.02–0.05 s of edge silence)
- QC: no clipping, no DC offset, no NaNs, 0.8–15 s duration,
  peak ≥ −40 dBFS (0 dropped clips)

## Reproducing

All scripts are Windows/PowerShell + Python (`soundfile`, `numpy`,
`num2words`):

```powershell
# 1. Build the prompt list (downloads Gutenberg books)
python scripts\build_prompts.py

# 2. Synthesize — 32-bit PowerShell is REQUIRED (SysWOW64), sharded:
$ps = "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
foreach ($i in 0..3) {
  Start-Process $ps -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass',
    '-File','scripts\synthesize.ps1','-ShardIndex',$i,'-ShardCount','4')
}

# 3. Trim + QC + metadata (budget-limited subset)
python scripts\postprocess.py
```

`synthesize.ps1` is resumable — existing WAVs are skipped, so interrupted
runs can simply be relaunched.

## License

[Unlicense](LICENSE). The recordings are synthetic speech generated from a
locally installed voice pack; the transcripts are public-domain. Use at your
own risk.
