from __future__ import annotations

from pathlib import Path
import unicodedata

import pandas as pd


def quitar_tildes(texto: str) -> str:
    protegido = str(texto).replace("ñ", "__enie_lower__").replace("Ñ", "__enie_upper__")
    normalizado = unicodedata.normalize("NFD", protegido)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    restaurado = unicodedata.normalize("NFC", sin_tildes)
    return restaurado.replace("__enie_lower__", "ñ").replace("__enie_upper__", "Ñ")


def normalizar_texto(texto: str) -> str:
    base = quitar_tildes(str(texto)).upper().strip()
    return " ".join(base.split())


def es_vacio(texto: object) -> bool:
    if texto is None:
        return True
    t = str(texto).strip().upper()
    return t in {"", "NA", "N/A", "NONE", "NULL", "NAN"}


def cargar_nombres(base_dir: Path) -> list[str]:
    nombres: set[str] = set()

    votantes_path = base_dir / "votantes_mazariegos_plazapublica_clean.csv"
    if votantes_path.exists():
        votantes = pd.read_csv(votantes_path, sep=",", keep_default_na=False)
        if "nombre" in votantes.columns:
            for value in votantes["nombre"].tolist():
                if not es_vacio(value):
                    nombres.add(normalizar_texto(value))

    for path in sorted(base_dir.glob("nominas_pago_usac_*_clean.csv")):
        df = pd.read_csv(path, sep=";", keep_default_na=False)
        col = "EMPLEADO_NORM" if "EMPLEADO_NORM" in df.columns else "EMPLEADO"
        if col in df.columns:
            for value in df[col].tolist():
                if not es_vacio(value):
                    nombres.add(normalizar_texto(value))

    for path in sorted(base_dir.glob("becas_usac_*_clean.csv")):
        df = pd.read_csv(path, sep=";", keep_default_na=False)
        col = "BENEFICIARIO_NORM" if "BENEFICIARIO_NORM" in df.columns else "BENEFICIARIO"
        if col in df.columns:
            for value in df[col].tolist():
                if not es_vacio(value):
                    nombres.add(normalizar_texto(value))

    return sorted(nombres)


def is_suffix_variant(shorter_tokens: list[str], longer_tokens: list[str]) -> bool:
    if len(longer_tokens) - len(shorter_tokens) != 1:
        return False
    if len(shorter_tokens) < 4:
        return False
    if shorter_tokens != longer_tokens[-len(shorter_tokens) :]:
        return False
    common_suffix = len(shorter_tokens)
    return common_suffix >= 3


def generar_alias_candidatos(
    base_dir: Path = Path("data/clean"),
    salida: Path = Path("data/clean/person_alias_candidates.csv"),
) -> Path:
    nombres = cargar_nombres(base_dir)

    grupos: dict[tuple[str, str], list[str]] = {}
    for nombre in nombres:
        tokens = nombre.split()
        if len(tokens) < 2:
            continue
        key = (tokens[-2], tokens[-1])
        grupos.setdefault(key, []).append(nombre)

    candidatos: list[dict[str, object]] = []
    vistos: set[tuple[str, str]] = set()

    for grupo_nombres in grupos.values():
        ordenados = sorted(grupo_nombres, key=lambda n: len(n.split()))
        for i in range(len(ordenados)):
            for j in range(i + 1, len(ordenados)):
                a = ordenados[i]
                b = ordenados[j]
                ta = a.split()
                tb = b.split()

                shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
                shorter_name, longer_name = (a, b) if len(ta) <= len(tb) else (b, a)

                if not is_suffix_variant(shorter, longer):
                    continue

                key = (shorter_name, longer_name)
                if key in vistos:
                    continue
                vistos.add(key)

                candidatos.append(
                    {
                        "alias_name": shorter_name,
                        "canonical_full_name": longer_name,
                        "rule": "suffix_plus_one_token",
                        "confidence": 0.97,
                        "needs_review": True,
                    }
                )

    df = pd.DataFrame(candidatos)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "alias_name",
                "canonical_full_name",
                "rule",
                "confidence",
                "needs_review",
            ]
        )

    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida, index=False)
    return salida


if __name__ == "__main__":
    output = generar_alias_candidatos()
    print(f"Candidatos de alias generados en: {output}")
