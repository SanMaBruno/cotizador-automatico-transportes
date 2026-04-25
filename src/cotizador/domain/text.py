from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    return without_accents.lower().replace("→", " ")

