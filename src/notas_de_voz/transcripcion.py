"""Formato común de una transcripción, independiente del motor que la produjo."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class Intervencion:
    hablante: str  # etiqueta del motor: "A", "B", ...
    inicio_ms: int
    fin_ms: int
    texto: str


@dataclass
class Transcripcion:
    motor: str
    duracion_s: float
    intervenciones: list[Intervencion]
    crudo: dict = field(default_factory=dict, repr=False)  # respuesta original del motor
    origen: dict = field(default_factory=dict)  # archivo, fecha, tipo y materia: lo que hace falta para rehacer la nota

    def hablantes(self) -> list[str]:
        return sorted({i.hablante for i in self.intervenciones})

    def como_texto(self, nombres: dict[str, str] | None = None, *, markdown: bool = True) -> str:
        """Una línea por intervención, `[hora · minuto] Hablante: texto` (o `[minuto]` si no se conoce la
        hora de grabación), con un separador donde empieza cada parte."""
        nombres = nombres or {}
        partes = self.origen.get("partes") or [{"archivo": self.origen.get("archivo", ""), "inicio_ms": 0}]
        actual = 0
        lineas = []
        for i in self.intervenciones:
            # Por el punto medio: el motor a veces marca el inicio de una frase unos ms antes del corte.
            while actual + 1 < len(partes) and (i.inicio_ms + i.fin_ms) // 2 >= partes[actual + 1]["inicio_ms"]:
                actual += 1
                p = partes[actual]
                separador = f"Parte {actual + 1} ({p['archivo']}) · empieza en {marca_de_tiempo(p['inicio_ms'], p)}"
                lineas.append(f"**— {separador} —**" if markdown else f"--- {separador} ---")
            quien = nombres.get(i.hablante, f"Hablante {i.hablante}")
            quien = f"**{quien}:**" if markdown else f"{quien}:"
            lineas.append(f"[{marca_de_tiempo(i.inicio_ms, partes[actual])}] {quien} {i.texto}")
        return "\n\n".join(lineas)

    def guardar(self, ruta: Path) -> None:
        ruta.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2))

    @classmethod
    def cargar(cls, ruta: Path) -> "Transcripcion":
        datos = json.loads(ruta.read_text())
        datos["intervenciones"] = [Intervencion(**i) for i in datos["intervenciones"]]
        return cls(**datos)


def marca_de_tiempo(ms: int, parte: dict) -> str:
    """`09:47 · 12:13`: la hora del reloj (para cruzar con lo anotado en papel) y el minuto del audio
    (para escucharlo). Solo el minuto si no se conoce la hora en que empezó esa parte."""
    if not parte.get("hora_inicio"):
        return formatear_tiempo(ms)
    hora = datetime.fromisoformat(parte["hora_inicio"]) + timedelta(milliseconds=ms - parte["inicio_ms"])
    return f"{hora:%H:%M} · {formatear_tiempo(ms)}"


def formatear_tiempo(ms: int) -> str:
    s = ms // 1000
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
