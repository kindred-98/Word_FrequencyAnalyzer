from typing import List
import re

from .models import AnalysisConfig

# ===============================
# NORMALIZAR TEXTO
# ===============================
def normalize_text(text: str, config: AnalysisConfig) -> str:
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\n", " ").replace("\t", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    if not getattr(config, "case_sensitive", False):
        normalized = normalized.lower()

    return normalized.strip()

# ===============================
# EXTRAER PALABRAS
# ===============================
def extract_words(text: str, config: AnalysisConfig) -> List[str]:
    if not text:
        return []

    words = re.findall(r"\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b", text)
    min_len = getattr(config, "min_word_length", 1)
    words = [w for w in words if len(w) >= min_len]

    if not getattr(config, "case_sensitive", False):
        words = [w.lower() for w in words]

    return words

# ===============================
# CONTAR ORACIONES
# ===============================
def count_sentences(text: str) -> int:
    if not text or not text.strip():
        return 0
    pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.?!])\s'
    sentences = re.split(pattern, text)
    return len([s for s in sentences if s.strip()])

# ===============================
# CONTAR PÁRRAFOS
# ===============================
def count_paragraphs(text: str) -> int:
    if not text or not text.strip():
        return 0
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r'\n\s*\n', normalized)
    return len([p for p in paragraphs if p.strip()])

# ===============================
# CONTAR CARACTERES
# ===============================
def count_characters(text: str) -> tuple[int, int]:
    total_chars = len(text)
    chars_no_spaces = len(re.sub(r'\s+', '', text))
    return total_chars, chars_no_spaces