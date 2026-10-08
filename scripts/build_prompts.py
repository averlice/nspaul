#!/usr/bin/env python3
"""Build prompts.tsv for the VW Paul dataset from Project Gutenberg books.

Pipeline per book: download -> strip PG boilerplate -> sentence split ->
digits->words -> abbreviation expansion -> charset/word-count filters ->
dedupe -> seeded shuffle -> prompts.tsv (id \t text).
"""
from __future__ import annotations

import random
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

from num2words import num2words

ROOT = Path(__file__).resolve().parent.parent
BOOK_DIR = ROOT / "data" / "gutenberg"
PROMPTS_OUT = ROOT / "prompts.tsv"

# Pre-1929 English prose (public domain in the US). Verified after download
# by size + English-stopword heuristics; failures are skipped.
BOOK_IDS = [
    1342, 84, 11, 1661, 2701, 98, 35, 36, 45, 55, 76, 74, 1260, 768, 43,
    844, 174, 205, 550, 1228, 2680, 499, 1232, 3710, 203, 829, 521, 62,
    118, 164, 2000, 135, 144, 145, 46, 766, 1400, 2346, 2852, 600, 341,
    12, 121, 141, 105, 158, 161, 1261, 1262, 1496, 4158, 1034, 34, 1080,
    1727, 1322, 1497, 2058, 17489, 1934, 2591, 4300, 1084, 1085, 1068,
    2600, 2805, 1389, 1407, 1509, 160, 1952, 219, 244, 3498, 4797, 514,
]

TARGET_PROMPTS = 7000
SEED = 20261007

ALLOWED = re.compile(r"^[A-Za-z][A-Za-z '\-,!?]*[.!?]?$|^[A-Za-z][A-Za-z '\-,!?]*$")
WORD = re.compile(r"\b\w+\b")

# --- text transformations -------------------------------------------------

ABBREV = {
    "mr.": "Mister", "mrs.": "Missus", "ms.": "Miss", "dr.": "Doctor",
    "prof.": "Professor", "rev.": "Reverend", "capt.": "Captain",
    "col.": "Colonel", "gen.": "General", "lt.": "Lieutenant",
    "sgt.": "Sergeant", "jr.": "Junior", "sr.": "Senior",
    "st.": "Saint", "mt.": "Mount", "no.": "number", "vs.": "versus",
    "etc.": "et cetera", "inc.": "Incorporated", "dept.": "Department",
    "univ.": "University", "est.": "established", "approx.": "approximately",
    "esq.": "Esquire", "hon.": "Honorable", "sgt.": "Sergeant",
}

ENGLISH_MARKERS = (
    " the ", " and ", " of ", " to ", " in ", " that ", " it ", " was ",
    " he ", " she ", " with ", " for ", " his ", " her ", " had ",
)

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
DIGIT_RANGE = re.compile(r"\d\s*[-\u2013\u2014]\s*\d")
ORD_SUFFIX = re.compile(r"\b(\d+)(st|nd|rd|th)\b", re.I)
GROUPED = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")
DECIMAL = re.compile(r"\b\d+\.\d+\b")
INTEGER = re.compile(r"\b\d+\b")
MULTISPACE = re.compile(r"\s+")
STRAIGHTEN = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
    "\u00ab": '"', "\u00bb": '"',
})


def digits_to_words(text: str) -> str:
    def ordinal(m: re.Match) -> str:
        return num2words(int(m.group(1)), to="ordinal")

    def grouped(m: re.Match) -> str:
        return num2words(float(m.group(0).replace(",", "")))

    def decimal(m: re.Match) -> str:
        return num2words(float(m.group(0)))

    def integer(m: re.Match) -> str:
        return num2words(int(m.group(0)))

    text = ORD_SUFFIX.sub(ordinal, text)
    text = GROUPED.sub(grouped, text)
    text = DECIMAL.sub(decimal, text)
    text = INTEGER.sub(integer, text)
    return text


def expand_abbrev(text: str) -> str:
    out: list[str] = []
    for tok in text.split(" "):
        key = tok.lower()
        if key in ABBREV:
            rep = ABBREV[key]
            out.append(rep + ("," if tok.endswith(",") else ""))
        else:
            out.append(tok)
    return " ".join(out)


def strip_boilerplate(raw: str) -> str:
    start = re.search(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG[^*]*\*\*\*", raw, re.I)
    end = re.search(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG[^*]*\*\*\*", raw, re.I)
    if start:
        raw = raw[start.end():]
    if end:
        raw = raw[: end.start()]
    return raw


def normalize(raw: str) -> str:
    raw = unicodedata.normalize("NFKC", raw)
    raw = raw.translate(STRAIGHTEN)
    # PG italic/underline markup markers
    raw = re.sub(r"[*_]", "", raw)
    return raw


def english_enough(text: str) -> bool:
    t = f" {text.lower()} "
    return sum(1 for m in ENGLISH_MARKERS if m in t) >= 4


def clean_sentence(s: str) -> str | None:
    s = MULTISPACE.sub(" ", s).strip()
    if not s or len(s) < 15:
        return None
    if DIGIT_RANGE.search(s):
        return None  # year ranges read unnaturally after conversion
    s = expand_abbrev(s)
    s = digits_to_words(s)
    s = MULTISPACE.sub(" ", s).strip()
    words = s.split()
    if not 4 <= len(words) <= 28:
        return None
    # drop ALL-CAPS tokens (acronyms/headings): engine may letter-spell them
    if any(w.isupper() and len(w) >= 2 for w in words):
        return None
    low = " " + s.lower() + " "
    if any(b in low for b in ("gutenberg", "transcriber", "ebook", "www.")):
        return None
    # no period inside tokens (leftover abbreviations / initials / decimals)
    if any("." in w[:-1] for w in words):
        return None
    if not ALLOWED.match(s):
        return None
    if not s[0].isalpha():
        return None
    if s[-1] not in ".!?":
        return None
    return s


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 50_000:
        return True
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nspaul-dataset/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) > 50_000:
                dest.write_bytes(data)
                return True
            return False
        except Exception as exc:  # noqa: BLE001 - network variability
            print(f"    attempt {attempt + 1} failed: {exc}", file=sys.stderr)
            time.sleep(1 + attempt * 2)
    return False


def main() -> int:
    BOOK_DIR.mkdir(parents=True, exist_ok=True)
    sentences: list[str] = []
    seen: set[str] = set()
    ok_books = 0

    print(f"Downloading up to {len(BOOK_IDS)} books...")
    for bid in BOOK_IDS:
        dest = BOOK_DIR / f"{bid}.txt"
        if not download(f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt", dest):
            print(f"  [{bid}] download failed, skipping")
            continue
        raw = dest.read_text(encoding="utf-8", errors="replace")
        body = normalize(strip_boilerplate(raw))
        if not english_enough(body[:20000]):
            print(f"  [{bid}] not English, skipping")
            continue
        ok_books += 1
        count_here = 0
        # PG plain text hard-wraps lines inside paragraphs: reflow first
        for para in re.split(r"\n\s*\n", body):
            para = MULTISPACE.sub(" ", para).strip()
            if len(para) < 30:
                continue
            for sent in SENT_SPLIT.split(para):
                cs = clean_sentence(sent)
                if cs is None:
                    continue
                key = cs.lower()
                if key in seen:
                    continue
                seen.add(key)
                sentences.append(cs)
                count_here += 1
        print(f"  [{bid}] +{count_here} sentences (total {len(sentences)})")

    print(f"\nBooks used: {ok_books}/{len(BOOK_IDS)}  unique sentences: {len(sentences)}")
    if len(sentences) < TARGET_PROMPTS:
        print("WARNING: fewer sentences than target", file=sys.stderr)

    random.Random(SEED).shuffle(sentences)
    chosen = sentences[:TARGET_PROMPTS]

    # final safety pass: no 'dataset' survives (engine mispronounces it)
    fixed = 0
    final: list[str] = []
    for s in chosen:
        new = re.sub(r"\bdatasets?\b", lambda m: m.group(0).replace("dataset", "data set"), s, flags=re.I)
        if new != s:
            fixed += 1
        if new not in seen or new in final:
            pass
        final.append(new)

    with PROMPTS_OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for i, s in enumerate(final):
            fh.write(f"{i:05d}\t{s}\n")

    print(f"Wrote {len(final)} prompts -> {PROMPTS_OUT} (dataset-fixes applied: {fixed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
