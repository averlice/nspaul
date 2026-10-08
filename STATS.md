# Dataset statistics

- Clips: **3697**
- Total duration: **5.15 h** (18546 s)
- Size on disk: **780.0 MB**
- Format: **22050 Hz**, mono, 16-bit PCM WAV
- Duration: min 0.80 s / median 4.62 s / max 14.57 s / mean 5.02 s
- QC: 0 clips rejected (silence/peak/duration), 3303 dropped for size budget
- Source prompts: 7000 sampled from 146587 unique sentences across 73 Gutenberg books

## Duration distribution

| range (s) | clips |
|---|---|
| 0-1 | 4 |
| 1-2 | 397 |
| 2-3 | 581 |
| 3-4 | 560 |
| 4-6 | 930 |
| 6-8 | 661 |
| 8-10 | 428 |
| 10-15 | 136 |

## Synthesis

- Voice: VW Paul (SAPI5, Voiceware), 32-bit engine
- Rate -2, volume 100 (engine defaults)
- Sharded synthesis: 4 x 1750 clips, 0 failures, 0 retries
