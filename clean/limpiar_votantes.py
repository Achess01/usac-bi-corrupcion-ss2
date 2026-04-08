from __future__ import annotations

from pathlib import Path
import unicodedata

import pandas as pd


CONNECTORES_APELLIDO = {
    "DA",
    "DAS",
    "DE",
    "DEL",
    "DELA",
    "DELAS",
    "DELOS",
    "DI",
    "DO",
    "DOS",
    "LA",
    "LAS",
    "LOS",
    "VAN",
    "VON",
    "Y",
}


def quitar_tildes(texto: str) -> str:
    protegido = str(texto).replace("ñ", "__enie_lower__").replace("Ñ", "__enie_upper__")
    normalizado = unicodedata.normalize("NFD", protegido)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    restaurado = unicodedata.normalize("NFC", sin_tildes)
    return restaurado.replace("__enie_lower__", "ñ").replace("__enie_upper__", "Ñ")


def normalizar_texto(texto: str) -> str:
    base = quitar_tildes(str(texto)).upper().strip()
    return " ".join(base.split())


def extraer_grupo_apellido(tokens: list[str], fin: int) -> tuple[list[str], int]:
    inicio = fin
    while inicio - 1 >= 0 and tokens[inicio - 1] in CONNECTORES_APELLIDO:
        inicio -= 1
    return tokens[inicio : fin + 1], inicio - 1


def apellidos_nombres(nombre_original: str) -> str:
    tokens = normalizar_texto(nombre_original).split()
    if len(tokens) <= 2:
        return " ".join(tokens)

    primer_apellido, indice = extraer_grupo_apellido(tokens, len(tokens) - 1)
    segundo_apellido: list[str] = []

    if indice >= 0:
        segundo_apellido, indice = extraer_grupo_apellido(tokens, indice)

    nombres = tokens[: indice + 1] if indice >= 0 else []
    partes_finales = segundo_apellido + primer_apellido + nombres
    return " ".join(parte for parte in partes_finales if parte)


def limpiar_votantes(
    archivo_entrada: Path = Path("data/raw/votantes_mazariegos_plazapublica.csv"),
    archivo_salida: Path = Path("data/clean/votantes_mazariegos_plazapublica_clean.csv"),
) -> None:
    df = pd.read_csv(archivo_entrada)

    df["nombre"] = df["nombre"].fillna("").map(apellidos_nombres)

    trabajo = df["trabajo_estado"].fillna("").map(normalizar_texto)
    trabajo = trabajo.replace({"": "NA", "N/A": "NA", "NULL": "NA", "NONE": "NA"})
    df["trabajo_estado"] = trabajo

    archivo_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(archivo_salida, index=False)


if __name__ == "__main__":
    limpiar_votantes()
