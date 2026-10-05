def format_analysis(result):
    """
    Convierte AnalysisResult en texto legible para GUI.
    """

    lines = ["📊 ESTADÍSTICAS DEL TEXTO\n"]

    lines.append(f"Caracteres: {result.num_characters}")
    lines.append(f"Caracteres sin espacios: {result.num_characters_no_spaces}")
    lines.append(f"Palabras: {result.num_words}")
    lines.append(f"Oraciones: {result.num_sentences}")
    lines.append(f"Párrafos: {result.num_paragraphs}")

    lines.append("\n📈 PALABRAS MÁS FRECUENTES\n")

    lines.extend(f"{word} → {freq}" for word, freq in result.most_common_words)

    if result.errors:
        lines.append("\n⚠️ ERRORES")
        lines.extend(result.errors)

    return "\n".join(lines)