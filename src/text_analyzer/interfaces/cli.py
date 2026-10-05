from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import track

from collections import Counter
import re
import time

from text_analyzer.core.analyzer import analyze_single_word, analyze_text, AnalysisResult, AnalysisConfig
from text_analyzer.io.exporter import export_json, export_csv, export_txt, export_word_json, export_word_csv, export_word_txt, EXPORT_DIR
from text_analyzer.login.logger import setup_logger
from text_analyzer.errors.error_handler import handle_error

logger = setup_logger()
console = Console()
historial = []

# ===============================
# MENSAJES REUTILIZABLES
# ===============================
MSG_FORMATO_INVALIDO = "[red]Formato inválido[/red]"
MSG_SIN_TEXTO = "[red]Aún no has analizado ningún texto. Ve al menú y usa la opción 1 primero.[/red]"
MSG_SIN_PALABRA = "[red]Aún no has analizado ninguna palabra. Ve al menú y usa la opción 2 primero.[/red]"

OPCION_TEXTO_DISPONIBLE = "[green]1) Análisis de texto completo[/green]"
OPCION_TEXTO_NO_DISPONIBLE = "[dim]1) Análisis de texto completo — no disponible (usa opción 1 del menú primero)[/dim]"
OPCION_PALABRA_DISPONIBLE = "[yellow]2) Análisis de palabra específica[/yellow]"
OPCION_PALABRA_NO_DISPONIBLE = "[dim]2) Análisis de palabra específica — no disponible (usa opción 2 del menú primero)[/dim]"

PATRON_PALABRA = r"\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+\b"

# ===============================
# Nuevo: ultimo_resultado ahora es AnalysisResult
# ===============================
ultimo_resultado: AnalysisResult | None = None
ultimo_resultado_palabra: dict | None = None

# ===============================
# MENÚ
# ===============================
def mostrar_menu():
    console.print(Panel("[bold cyan]📂 MENÚ DEL ANALIZADOR DE TEXTO[/bold cyan]", subtitle="Selecciona una opción", expand=False))
    console.print("[green]1) Analizar texto completo[/green] 📄")
    console.print("[yellow]2) Analizar palabra específica[/yellow] 🔍")
    console.print("[magenta]3) Ver historial de análisis[/magenta] 📜")
    console.print("[blue]4) Exportar resultados[/blue] 💾")
    console.print("[red]5) Salir[/red] ❌")
    opcion = Prompt.ask("Ingresa el número de la opción")
    return opcion

# ===============================
# ANALIZAR TEXTO (AHORA DEVUELVE AnalysisResult REAL)
# ===============================
def analizar_texto():
    global ultimo_resultado

    logger.info("CLI: usuario inició análisis de texto")
    texto = Prompt.ask("\nIngresa el texto a analizar 📄")

    if not texto.strip():
        logger.warning("CLI: El texto ingresado está vacío")
        console.print("[red]Texto vacío. Intenta de nuevo.[/red]")
        return ""

    console.print("\n[bold green]Analizando texto...[/bold green]")
    for _ in track(range(50), description="Procesando..."):
        time.sleep(0.01)

    config = AnalysisConfig(top_n=10)
    result = analyze_text(texto, config=config)
    ultimo_resultado = result  # Guardamos el objeto AnalysisResult real

    # Panel resumen usando texto original o capitalización ligera
    analisis_panel = (
        f"[bold green]Total palabras:[/bold green] {result.num_words} | "
        f"[bold green]Total caracteres:[/bold green] {result.num_characters} | "
        f"[bold yellow]Palabra más frecuente:[/bold yellow] "
        f"'{result.most_common_words[0][0].capitalize()}' ({result.most_common_words[0][1]} veces)" 
        if result.most_common_words else ""
    )

    console.print(Panel(analisis_panel, title="✅ Estadísticas Generales", expand=False))

    table = Table(title="📊 Palabras más frecuentes", show_lines=True)
    table.add_column("Palabra", style="cyan", no_wrap=True)
    table.add_column("Frecuencia", style="magenta")
    table.add_column("Visual", style="green")

    max_freq = result.most_common_words[0][1] if result.most_common_words else 1
    for palabra, freq in result.most_common_words:
        bar = "█" * int((freq / max_freq) * 20)
        table.add_row(palabra.capitalize(), str(freq), bar)

    console.print(table)
    guardar_historial(analisis_panel)
    logger.info("CLI: análisis de texto completado")
    return texto
# ===============================
# ANALIZAR PALABRA
# ===============================
def analizar_palabra(texto):
    global ultimo_resultado_palabra

    if not texto:
        logger.warning("CLI: intento de analizar palabra sin texto previo")
        console.print("[red]Primero debes analizar un texto completo.[/red]")
        return

    palabra_input = Prompt.ask("Ingresa la palabra a analizar 🔍")
    palabra = palabra_input.lower()  # solo para conteo interno

    palabras_normalizadas = re.findall(PATRON_PALABRA, ultimo_resultado.normalized_text) if ultimo_resultado else []
    contador = ultimo_resultado.word_frequencies.get(palabra, 0) if ultimo_resultado else 0
    posiciones = [i + 1 for i, p in enumerate(palabras_normalizadas) if p == palabra]

    linguistic = analyze_single_word(palabra)

    analisis = (
        f"[bold yellow]Palabra:[/bold yellow] '{palabra_input}' | "
        f"[bold cyan]Veces encontrada:[/bold cyan] {contador} | "
        f"[bold magenta]Posiciones:[/bold magenta] {posiciones}"
    )

    console.print(Panel(analisis, title="🔎 Resultado Palabra", expand=False))

    table = Table(title="🧠 Análisis Lingüístico", show_lines=True)
    table.add_column("Propiedad", style="cyan")
    table.add_column("Valor", style="green")
    table.add_row("Palabra", linguistic["word"])
    table.add_row("Sílabas", "-".join(linguistic["syllables"]))
    table.add_row("Número de sílabas", str(linguistic["syllable_count"]))
    table.add_row("Tiene tilde", "Sí" if linguistic["has_tilde"] else "No")
    table.add_row("Tipo de palabra", linguistic["stress_type"])

    console.print(table)
    guardar_historial(analisis)

    ultimo_resultado_palabra = {
        **linguistic,
        "count": contador,
        "positions": posiciones,
    }

    logger.info(f"CLI: análisis de palabra '{palabra_input}' completado")

# ===============================
# HISTORIAL
# ===============================

def guardar_historial(analisis: str | AnalysisResult):
    """
    Añade al historial un registro de análisis en formato string.
    - Si recibe AnalysisResult, genera un resumen legible.
    - Si recibe str, lo guarda tal cual.
    """
    if isinstance(analisis, AnalysisResult):
        resumen = (
            f"Palabras: {analisis.num_words}, "
            f"Caracteres: {analisis.num_characters}, "
            f"Top: {', '.join([w for w, _ in analisis.most_common_words[:5]])}"
        )
        historial.append(resumen)
    else:
        historial.append(str(analisis))


def ver_historial():
    """
    Muestra en consola el historial de análisis de texto.
    Compatible con strings y AnalysisResult (resumidos).
    """
    logger.info("CLI: usuario consultó historial")

    if historial:
        console.print(Panel("[bold magenta]📜 HISTORIAL DE ANÁLISIS[/bold magenta]", expand=False))

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("N°")
        table.add_column("Resultado")

        for i, h in enumerate(historial, 1):
            table.add_row(str(i), h)

        console.print(table)
    else:
        logger.warning("CLI: historial consultado pero está vacío")
        console.print("[red]No hay historial disponible.[/red]")

# ===============================
# EXPORTAR RESULTADOS
# ===============================
def elegir_objetivo_exportacion() -> str | None:
    """
    Muestra las opciones de exportación y devuelve el objetivo elegido
    ("texto" o "palabra"), o None si no se puede exportar.
    """

    console.print("\n[bold cyan]¿Qué quieres exportar?[/bold cyan]")
    console.print(OPCION_TEXTO_DISPONIBLE if ultimo_resultado else OPCION_TEXTO_NO_DISPONIBLE)
    console.print(OPCION_PALABRA_DISPONIBLE if ultimo_resultado_palabra else OPCION_PALABRA_NO_DISPONIBLE)

    tipo = Prompt.ask("Selecciona qué exportar (1 o 2)")

    if tipo == "1":
        if not ultimo_resultado:
            console.print(MSG_SIN_TEXTO)
            return None
        return "texto"

    if tipo == "2":
        if not ultimo_resultado_palabra:
            console.print(MSG_SIN_PALABRA)
            return None
        return "palabra"

    console.print(MSG_FORMATO_INVALIDO)
    return None


def elegir_formato_exportacion() -> str:
    """
    Muestra los formatos disponibles y devuelve la opción elegida.
    """

    console.print("\n[bold cyan]Formato de exportación[/bold cyan]")
    console.print("1) TXT")
    console.print("2) JSON")
    console.print("3) CSV")
    console.print(f"[dim]Los archivos se guardarán en:[/dim] {EXPORT_DIR}")

    return Prompt.ask("Selecciona formato")


def obtener_exportador(objetivo: str, opcion: str):
    """
    Devuelve la función exportadora correspondiente, o None si el formato no existe.
    """

    if objetivo == "texto":
        return {"1": export_txt, "2": export_json, "3": export_csv}.get(opcion)

    return {"1": export_word_txt, "2": export_word_json, "3": export_word_csv}.get(opcion)


def exportar_resultados():
    if not ultimo_resultado and not ultimo_resultado_palabra:
        logger.warning("CLI: intento de exportar sin análisis previo")
        console.print("[red]Primero debes analizar un texto o una palabra.[/red]")
        return

    objetivo = elegir_objetivo_exportacion()

    if objetivo is None:
        return

    fn = obtener_exportador(objetivo, elegir_formato_exportacion())

    if not fn:
        console.print(MSG_FORMATO_INVALIDO)
        return

    datos = ultimo_resultado if objetivo == "texto" else ultimo_resultado_palabra
    filename = fn(datos)

    logger.info(f"CLI: resultados exportados a {filename}")
    console.print(f"[green]Archivo exportado:[/green] {filename}")
    console.print(f"[dim]Carpeta:[/dim] {EXPORT_DIR}")
    
# ===============================
# RUN CLI
# ===============================
def run_cli():
    texto = ""
    logger.info("CLI iniciado")
    while True:
        try:
            opcion = mostrar_menu()
            if opcion == "1":
                texto = analizar_texto()
            elif opcion == "2":
                analizar_palabra(texto)
            elif opcion == "3":
                ver_historial()
            elif opcion == "4":
                exportar_resultados()
            elif opcion == "5":
                logger.info("CLI finalizado por el usuario")
                console.print("[bold red]¡Hasta luego![/bold red] 👋")
                break
            else:
                console.print("[red]Opción inválida.[/red]")
        except Exception as e:
            handle_error(e)

# ===============================
# GUI SUPPORT / TEST COMPATIBILITY
# ===============================
def format_analysis_report(result: AnalysisResult | str) -> str:
    """
    Función para compatibilidad con tests antiguos.
    Si recibe AnalysisResult devuelve un resumen básico,
    si recibe string devuelve el mismo string.
    """
    if isinstance(result, AnalysisResult):
        return f"Texto: {result.raw_text}\nPalabras: {result.num_words}"
    return str(result)