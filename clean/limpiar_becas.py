from __future__ import annotations

from pathlib import Path
import re
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
    return " ".join(segundo_apellido + primer_apellido + nombres)


def extraer_anio_archivo(nombre_archivo: str) -> int:
    match = re.search(r"becas_usac_(\d{4})\.csv$", nombre_archivo)
    if not match:
        raise ValueError(f"Nombre de archivo no esperado: {nombre_archivo}")
    return int(match.group(1))


def limpiar_archivo(archivo_entrada: Path, directorio_salida: Path) -> Path:
    anio_archivo = extraer_anio_archivo(archivo_entrada.name)
    df = pd.read_csv(archivo_entrada, sep=";")

    if "MONTO" in df.columns:
        df["MONTO"] = pd.to_numeric(df["MONTO"], errors="coerce")

    if "FECHA DE INICIO" in df.columns:
        df["fecha_inicio"] = pd.to_datetime(
            df["FECHA DE INICIO"], format="%d-%m-%Y", errors="coerce"
        )
    if "FECHA FIN" in df.columns:
        df["fecha_fin"] = pd.to_datetime(
            df["FECHA FIN"], format="%d-%m-%Y", errors="coerce"
        )

    if "fecha_inicio" in df.columns and "fecha_fin" in df.columns:
        df["flag_fechas_invertidas"] = df["fecha_inicio"] > df["fecha_fin"]
        df["flag_anio_inicio_inconsistente"] = df["fecha_inicio"].dt.year != anio_archivo

    if "BENEFICIARIO" in df.columns:
        df["BENEFICIARIO"] = df["BENEFICIARIO"].fillna("").map(apellidos_nombres)
        df["BENEFICIARIO_NORM"] = df["BENEFICIARIO"]
    if "TIPO DE BECA" in df.columns:
        df["TIPO_BECA_NORM"] = df["TIPO DE BECA"].fillna("").map(normalizar_texto)

    directorio_salida.mkdir(parents=True, exist_ok=True)
    salida = directorio_salida / archivo_entrada.name.replace(".csv", "_clean.csv")
    df.to_csv(salida, sep=";", index=False)
    return salida


def limpiar_becas(
    directorio_entrada: Path = Path("data/raw"),
    directorio_salida: Path = Path("data/clean"),
) -> list[Path]:
    archivos = sorted(directorio_entrada.glob("becas_usac_*.csv"))
    return [limpiar_archivo(archivo, directorio_salida) for archivo in archivos]


if __name__ == "__main__":
    limpiar_becas()
