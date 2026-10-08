"""`notas diagnostico`: revisa que todo esté listo para procesar, sin gastar nada."""

import platform
import shutil
import subprocess

import httpx

from .config import PERFIL, RAIZ, VOCABULARIO, Config
from .motores.assemblyai import BASE


def diagnosticar(config: Config) -> bool:
    """Imprime una línea por cada requisito y devuelve si están todos los indispensables."""
    ok = True

    def informar(estado: str, texto: str) -> None:
        print(f"  {estado} {texto}")

    if platform.system() == "Darwin":
        informar("✓", "macOS")
    else:
        informar("!", f"{platform.system()}: el proyecto está probado solo en macOS. Unir partes y la carpeta "
                      "de iCloud no van a funcionar; un audio suelto con `notas procesar`, quizá sí.")

    if shutil.which("claude"):
        version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
        informar("✓", f"Claude Code instalado ({version})")
    else:
        ok = False
        informar("✗", "Falta Claude Code (el comando `claude`): https://claude.com/claude-code")

    if not (RAIZ / ".env").exists():
        informar("!", "No hay archivo .env: copiá .env.example como .env")
    if config.motor == "assemblyai":
        if not config.assemblyai_api_key:
            ok = False
            informar("✗", "Falta ASSEMBLYAI_API_KEY en .env: https://www.assemblyai.com/dashboard")
        else:
            try:
                respuesta = httpx.get(f"{BASE}/transcript", params={"limit": 1}, timeout=20,
                                      headers={"authorization": config.assemblyai_api_key})
                if respuesta.status_code == 200:
                    informar("✓", "La clave de AssemblyAI funciona")
                else:
                    ok = False
                    informar("✗", f"AssemblyAI rechazó la clave (HTTP {respuesta.status_code}): revisala en .env")
            except httpx.HTTPError as e:
                ok = False
                informar("✗", f"No se pudo hablar con AssemblyAI: {e}")

    if shutil.which("afconvert"):
        informar("✓", "afconvert (para unir grabaciones en varias partes)")
    else:
        informar("!", "Falta afconvert: no se pueden unir grabaciones en varias partes")

    if PERFIL.exists():
        informar("✓", "perfil.md")
    else:
        informar("!", "No hay perfil.md (opcional, mejora las notas): copiá perfil.example.md como perfil.md")

    vocabularios = [v.stem for v in VOCABULARIO.glob("*.txt") if v.stem != "ejemplo"]
    informar("·", f"Vocabularios: {', '.join(vocabularios) if vocabularios else 'ninguno (opcional)'}")

    if config.carpeta_entrada.exists():
        informar("✓", f"Carpeta de entrada: {config.carpeta_entrada}")
    else:
        informar("·", "Sin carpeta de entrada (solo hace falta para el Atajo de iOS: `notas preparar`)")
    informar("·", f"Las notas se guardan en {config.carpeta_salida}")

    print("\nListo para procesar." if ok else "\nFalta configurar lo marcado con ✗.")
    return ok
