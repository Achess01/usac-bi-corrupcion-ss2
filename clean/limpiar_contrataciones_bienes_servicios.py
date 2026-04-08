from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import pandas as pd


NUMERIC_COLS = ["UNIDADES", "PRECIO UNITARIO", "MONTO TOTAL"]
TEXT_COLS = ["UNIDAD", "DESCRIPCION DEL GASTO", "NOMBRE DEL PROVEEDOR"]

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
    normalizado = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", sin_tildes)


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
    return " ".join(segundo_apellido + primer_apellido + nombres)


def extraer_anio_archivo(nombre_archivo: str) -> int:
    match = re.search(
        r"contrataciones_bienes_servicios_usac_(\d{4})\.csv$", nombre_archivo
    )
    if not match:
        raise ValueError(f"Nombre de archivo no esperado: {nombre_archivo}")
    return int(match.group(1))


def limpiar_archivo(archivo_entrada: Path, directorio_salida: Path) -> Path:
    anio_archivo = extraer_anio_archivo(archivo_entrada.name)
    df = pd.read_csv(archivo_entrada, sep=";")

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "FECHA" in df.columns:
        df["fecha"] = pd.to_datetime(df["FECHA"], format="%d/%m/%y", errors="coerce")
        df["anio_fecha"] = df["fecha"].dt.year
        df["flag_anio_inconsistente"] = df["anio_fecha"] != anio_archivo
    else:
        df["flag_anio_inconsistente"] = pd.NA

    for col in TEXT_COLS:
        if col in df.columns:
            df[f"{col}_NORM"] = df[col].fillna("").map(normalizar_texto)

    if "NOMBRE DEL PROVEEDOR" in df.columns:
        df["NOMBRE DEL PROVEEDOR"] = (
            df["NOMBRE DEL PROVEEDOR"].fillna("").map(apellidos_nombres)
        )
        df["NOMBRE DEL PROVEEDOR_NORM"] = df["NOMBRE DEL PROVEEDOR"]

    if "NIT DEL PROVEEDOR" in df.columns:
        nit = df["NIT DEL PROVEEDOR"].astype(str).str.strip()
        df["NIT_PROVEEDOR_NORM"] = nit.str.replace(r"\D", "", regex=True)

    directorio_salida.mkdir(parents=True, exist_ok=True)
    salida = directorio_salida / archivo_entrada.name.replace(".csv", "_clean.csv")
    df.to_csv(salida, sep=";", index=False)
    return salida


def limpiar_contrataciones_bienes_servicios(
    directorio_entrada: Path = Path("data/raw"),
    directorio_salida: Path = Path("data/clean"),
) -> list[Path]:
    archivos = sorted(
        directorio_entrada.glob("contrataciones_bienes_servicios_usac_*.csv")
    )
    return [limpiar_archivo(archivo, directorio_salida) for archivo in archivos]


if __name__ == "__main__":
    limpiar_contrataciones_bienes_servicios()
