def format_analysis(result):
    """
    Convierte AnalysisResult en texto legible para GUI.
    """

    lines = ["📊 ESTADÍSTICAS DEL TEXTO\n"]

    lines.extend([
        f"Caracteres: {result.num_characters}",
        f"Caracteres sin espacios: {result.num_characters_no_spaces}",
        f"Palabras: {result.num_words}",
        f"Oraciones: {result.num_sentences}",
        f"Párrafos: {result.num_paragraphs}",
        "\n📈 PALABRAS MÁS FRECUENTES\n",
    ])

    lines.extend(f"{word} → {freq}" for word, freq in result.most_common_words)

    if result.errors:
        lines.append("\n⚠️ ERRORES")
        lines.extend(result.errors)

    return "\n".join(lines)