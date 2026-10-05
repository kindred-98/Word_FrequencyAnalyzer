# src/text_analyzer/io/file_loader.py

"""
Lectura y escritura de archivos .txt con manejo robusto de errores.
Usa open() con context managers (with) y encodings múltiples.
"""

import os
from pathlib import Path
from typing import Optional

from ..core.analyzer import analyze_text
from ..core.models import AnalysisResult, FileAnalysisContext, AnalysisConfig


class FileReadError(Exception):
    """Excepción personalizada para errores de lectura."""
    pass


class FileWriteError(Exception):
    """Excepción personalizada para errores de escritura."""
    pass


def read_text_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Lee contenido completo de archivo .txt con manejo de encodings.
    
    Args:
        file_path: Ruta al archivo
        encoding: Codificación a intentar (default utf-8)
        
    Returns:
        Contenido del archivo como string
        
    Raises:
        FileReadError: Si no puede leer el archivo (no existe, permisos, encoding)
    """
    path = Path(file_path)
    
    if not path.is_file():
        raise FileReadError(f"Archivo no encontrado: {file_path}")
    
    if path.suffix.lower() != ".txt":
        raise FileReadError(f"Solo se permiten archivos .txt, recibido: {file_path}")
    
    # Solo encodings estrictos
    encodings_to_try = [encoding, "utf-8-sig"]
    last_error = None

    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except OSError as e:
            raise FileReadError(f"Error de permisos o acceso: {e}")

    # Si ningún encoding funcionó, lanzamos excepción
    raise FileReadError(
        f"No se pudo leer {file_path} con ningún encoding conocido. Último error: {last_error}"
    )

def write_text_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """
    Escribe texto a archivo con manejo de errores.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
    except OSError as e:
        raise FileWriteError(f"Error escribiendo {file_path}: {e}")


def analyze_file(file_path: str, config: AnalysisConfig | None = None) -> FileAnalysisContext:
    """
    Análisis completo de archivo: leer + analizar + contexto.
    """
    try:
        content = read_text_file(file_path)
        result = analyze_text(content, config)
        return FileAnalysisContext(
            file_path=str(Path(file_path).absolute()),
            encoding="utf-8",
            result=result,
            read_error=None
        )
    except FileReadError as e:
        return FileAnalysisContext(
            file_path=str(Path(file_path).absolute()),
            encoding="utf-8",
            result=None,
            read_error=str(e)
        )