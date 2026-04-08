from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import pandas as pd


NUMERIC_COLS = ["CANTIDAD", "PRECIO UNITARIO", "PRECIO TOTAL"]
TEXT_COLS = ["UNIDAD EJECUTORA", "DESCRIPCION DE LA COMPRA", "PROVEEDOR"]


def quitar_tildes(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", sin_tildes)


def normalizar_texto(texto: str) -> str:
    base = quitar_tildes(str(texto)).upper().strip()
    return " ".join(base.split())


def extraer_anio_archivo(nombre_archivo: str) -> int:
    match = re.search(r"compras_directas_usac_(\d{4})\.csv$", nombre_archivo)
    if not match:
        raise ValueError(f"Nombre de archivo no esperado: {nombre_archivo}")
    return int(match.group(1))


def limpiar_archivo(archivo_entrada: Path, directorio_salida: Path) -> Path:
    anio_archivo = extraer_anio_archivo(archivo_entrada.name)
    df = pd.read_csv(archivo_entrada, sep=";")

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "FECHA LIQUIDACION" in df.columns:
        df["fecha_liquidacion"] = pd.to_datetime(
            df["FECHA LIQUIDACION"], errors="coerce"
        )
        df["anio_fecha_liquidacion"] = df["fecha_liquidacion"].dt.year
        df["flag_anio_inconsistente"] = df["anio_fecha_liquidacion"] != anio_archivo
    else:
        df["flag_anio_inconsistente"] = pd.NA

    for col in TEXT_COLS:
        if col in df.columns:
            df[f"{col}_NORM"] = df[col].fillna("").map(normalizar_texto)

    if "NIT" in df.columns:
        nit = df["NIT"].astype(str).str.strip()
        df["NIT_NORM"] = nit.str.replace(r"\D", "", regex=True)

    directorio_salida.mkdir(parents=True, exist_ok=True)
    salida = directorio_salida / archivo_entrada.name.replace(".csv", "_clean.csv")
    df.to_csv(salida, sep=";", index=False)
    return salida


def limpiar_compras_directas(
    directorio_entrada: Path = Path("data/raw"),
    directorio_salida: Path = Path("data/clean"),
) -> list[Path]:
    archivos = sorted(directorio_entrada.glob("compras_directas_usac_*.csv"))
    return [limpiar_archivo(archivo, directorio_salida) for archivo in archivos]


if __name__ == "__main__":
    limpiar_compras_directas()
