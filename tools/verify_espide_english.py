#!/usr/bin/env python3
"""Catch non-ASCII source and known Czech text in ESP IDE firmware sources.

This is a regression guard, not a general-purpose language detector. New
libraries still need an English-language review before they are frozen.
"""

import io
from pathlib import Path
import re
import sys
import tokenize

BASE = Path(__file__).resolve().parents[1] / "ports/esp32/boards/ESPIDE"
CZECH_TEXT = re.compile(
    r"\b(?:chyba|chyby|chybu|nebyl|povolen|nazev|znaku|programu|"
    r"cteni|soubor|souboru|knihovny|nedostatek|zastaveni|spatne|spatny|"
    r"pouzita|promenna|neexistuje|objekt|deleni|zkontroluj|startuji|"  # codespell:ignore objekt
    r"nepouziva|hodnoty|hodnotu|puvodni|vraci|vracim|blokuju|"
    r"dalkomerem|predpocty|zaoblene|barvy|vicka|rozmery|roztec|"
    r"prepinace|parametry|serazeni|horni|dolni|levy|pravy|leve|prave|"  # codespell:ignore leve
    r"kresleni|logika|smysce|smycce|pokracuj|ochrana|usporne|"
    r"potrebujeme|zaoblovat|tupliky|prijima|vytvor|mezery|lokalni)\b",
    re.IGNORECASE,
)


def check_file(path):
    text = path.read_text(encoding="utf-8")
    errors = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.isascii():
            errors.append(f"{path}:{number}: non-ASCII source text")
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING) and CZECH_TEXT.search(token.string):
            errors.append(f"{path}:{token.start[0]}: known Czech text in comment or message")
    return errors


def main():
    paths = sorted((BASE / "modules").glob("*.py")) + sorted((BASE / "filesystem").glob("*.py"))
    errors = [error for path in paths for error in check_file(path)]
    if errors:
        sys.exit("\n".join(errors))
    print(f"English source guard passed: {len(paths)} firmware Python files")


if __name__ == "__main__":
    main()
