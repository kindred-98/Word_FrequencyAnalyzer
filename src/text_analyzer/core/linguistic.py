"""
Módulo de análisis lingüístico de palabras en español.
"""

import re
from dataclasses import dataclass


VOWELS = "aeiouáéíóúü"

STRESS_BY_POSITION = {
    1: "aguda",
    2: "grave",
    3: "esdrújula",
}


@dataclass
class WordAnalysis:
    word: str
    syllables: list[str]
    syllable_count: int
    has_tilde: bool
    stress_type: str


def split_syllables(word: str) -> list[str]:
    """
    División simple aproximada de sílabas.
    No es perfecta pero funciona bien para español común.
    """

    pattern = r'[^aeiouáéíóúü]*[aeiouáéíóúü]+'
    syllables = re.findall(pattern, word.lower())

    if not syllables:
        return [word]

    return syllables


def has_accent(word: str) -> bool:
    """
    Detecta si la palabra tiene tilde.
    """
    return any(c in "áéíóú" for c in word.lower())


def find_accent_position(syllables: list[str]) -> int | None:
    """
    Devuelve la posición de la sílaba tildada contando desde el final,
    o None si ninguna sílaba tiene tilde.
    """

    count = len(syllables)

    for index, syllable in enumerate(syllables):
        if has_accent(syllable):
            return count - index

    return None


def detect_stress_type(word: str, syllables: list[str]) -> str:
    """
    Determina si es:
    aguda
    grave (llana)
    esdrújula
    sobresdrújula
    """

    count = len(syllables)

    if count == 1:
        return "monosílaba"

    if has_accent(word):
        position = find_accent_position(syllables)

        if position is not None:
            return STRESS_BY_POSITION.get(position, "sobresdrújula")

    # reglas generales
    if word.endswith(("n", "s")) or word[-1] in VOWELS:
        return "grave"

    return "aguda"


def analyze_word_linguistics(word: str) -> WordAnalysis:
    """
    Analiza lingüísticamente una palabra.
    """

    syllables = split_syllables(word)

    stress_type = detect_stress_type(word, syllables)

    return WordAnalysis(
        word=word,
        syllables=syllables,
        syllable_count=len(syllables),
        has_tilde=has_accent(word),
        stress_type=stress_type,
    )