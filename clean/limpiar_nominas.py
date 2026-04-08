from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import pandas as pd


NUMERIC_COLS = [
    "SUELDO BASE",
    "ESCALAFON",
    "COMP.",
    "NOMINAL",
    "BONO M.",
    "TOT. DCTOS.",
    "LIQUIDO",
]


def quitar_tildes(texto: str) -> str:
    protegido = str(texto).replace("ñ", "__enie_lower__").replace("Ñ", "__enie_upper__")
    normalizado = unicodedata.normalize("NFD", protegido)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    restaurado = unicodedata.normalize("NFC", sin_tildes)
    return restaurado.replace("__enie_lower__", "ñ").replace("__enie_upper__", "Ñ")


def normalizar_texto(texto: str) -> str:
    base = quitar_tildes(str(texto)).upper().strip()
    return " ".join(base.split())


def extraer_periodo_archivo(nombre_archivo: str) -> tuple[int, int]:
    patron = r"nominas_pago_usac_(\d{4})_(\d{2})\.csv$"
    match = re.search(patron, nombre_archivo)
    if not match:
        raise ValueError(f"Nombre de archivo no esperado: {nombre_archivo}")
    return int(match.group(1)), int(match.group(2))


def extraer_mes_anio_pago(valor: str) -> tuple[float, float]:
    texto = str(valor).strip()
    if "/" not in texto:
        return pd.NA, pd.NA
    partes = texto.split("/")
    if len(partes) != 2:
        return pd.NA, pd.NA
    try:
        mes = int(partes[0])
        anio = int(partes[1])
    except ValueError:
        return pd.NA, pd.NA
    return mes, anio


def limpiar_archivo_nomina(archivo_entrada: Path, directorio_salida: Path) -> Path:
    anio_archivo, mes_archivo = extraer_periodo_archivo(archivo_entrada.name)

    df = pd.read_csv(archivo_entrada, sep=";")

    if "EMPLEADO" in df.columns:
        df["EMPLEADO_NORM"] = df["EMPLEADO"].fillna("").map(normalizar_texto)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    mes_anio = df.get("MES DE PAGO", pd.Series([pd.NA] * len(df))).map(extraer_mes_anio_pago)
    df["mes_pago"] = mes_anio.map(lambda x: x[0])
    df["anio_pago"] = mes_anio.map(lambda x: x[1])

    df["mes_archivo"] = mes_archivo
    df["anio_archivo"] = anio_archivo

    df["flag_periodo_inconsistente"] = (
        (df["mes_pago"] != df["mes_archivo"]) | (df["anio_pago"] != df["anio_archivo"])
    )

    directorio_salida.mkdir(parents=True, exist_ok=True)
    salida = directorio_salida / archivo_entrada.name.replace(".csv", "_clean.csv")
    df.to_csv(salida, sep=";", index=False)
    return salida


def limpiar_nominas(
    directorio_entrada: Path = Path("data/raw"),
    directorio_salida: Path = Path("data/clean"),
) -> list[Path]:
    archivos = sorted(directorio_entrada.glob("nominas_pago_usac_*.csv"))
    salidas = []
    for archivo in archivos:
        salidas.append(limpiar_archivo_nomina(archivo, directorio_salida))
    return salidas


if __name__ == "__main__":
    limpiar_nominas()
