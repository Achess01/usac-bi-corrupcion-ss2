from __future__ import annotations

import argparse
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


CONNECTORES = {
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


@dataclass
class DatasetGroup:
    votantes: pd.DataFrame
    nominas: pd.DataFrame
    compras: pd.DataFrame
    contrataciones: pd.DataFrame
    becas: pd.DataFrame


def quitar_tildes(texto: str) -> str:
    protegido = str(texto).replace("ñ", "__enie_lower__").replace("Ñ", "__enie_upper__")
    normalizado = unicodedata.normalize("NFD", protegido)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    restaurado = unicodedata.normalize("NFC", sin_tildes)
    return restaurado.replace("__enie_lower__", "ñ").replace("__enie_upper__", "Ñ")


def normalizar_texto(texto: str) -> str:
    base = quitar_tildes(texto).upper().strip()
    return " ".join(base.split())


def valor_nulo(texto: object) -> bool:
    if texto is None:
        return True
    t = str(texto).strip().upper()
    return t in {"", "NA", "N/A", "NONE", "NULL", "NAN"}


def cargar_csv(path: Path, sep: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=sep, keep_default_na=False)


def cargar_datasets(base_dir: Path = Path("data/clean")) -> DatasetGroup:
    votantes_path = base_dir / "votantes_mazariegos_plazapublica_clean.csv"
    votantes = cargar_csv(votantes_path, sep=",")

    nominas = pd.concat(
        [cargar_csv(p, sep=";") for p in sorted(base_dir.glob("nominas_pago_usac_*_clean.csv"))],
        ignore_index=True,
    )
    compras = pd.concat(
        [cargar_csv(p, sep=";") for p in sorted(base_dir.glob("compras_directas_usac_*_clean.csv"))],
        ignore_index=True,
    )
    contrataciones = pd.concat(
        [
            cargar_csv(p, sep=";")
            for p in sorted(base_dir.glob("contrataciones_bienes_servicios_usac_*_clean.csv"))
        ],
        ignore_index=True,
    )
    becas = pd.concat(
        [cargar_csv(p, sep=";") for p in sorted(base_dir.glob("becas_usac_*_clean.csv"))],
        ignore_index=True,
    )
    return DatasetGroup(votantes, nominas, compras, contrataciones, becas)


def split_dependencia_unidad(valor: object) -> tuple[str | None, str | None]:
    if valor_nulo(valor):
        return None, None

    texto = normalizar_texto(str(valor))

    if "--" in texto:
        dep, uni = texto.split("--", 1)
        return dep.strip() or None, uni.strip() or None

    if " - " in texto:
        dep, uni = texto.split(" - ", 1)
        return dep.strip() or None, uni.strip() or None

    return None, texto


def cargar_alias_personas(path: Path = Path("data/clean/person_alias_map.csv")) -> dict[str, str]:
    if not path.exists():
        return {}

    alias_df = pd.read_csv(path, keep_default_na=False)
    if "alias_name" not in alias_df.columns or "canonical_full_name" not in alias_df.columns:
        return {}

    if "approved_manual" in alias_df.columns:
        aprobados = alias_df["approved_manual"].astype(str).str.strip().str.lower()
        permitidos = {"1", "true", "t", "yes", "y", "si", "sí"}
        alias_df = alias_df[aprobados.isin(permitidos)]

    alias_map: dict[str, str] = {}
    for _, row in alias_df.iterrows():
        alias = normalizar_texto(row["alias_name"])
        canonical = normalizar_texto(row["canonical_full_name"])
        if alias and canonical:
            alias_map[alias] = canonical
    return alias_map


def canonical_person_name(name: object, alias_map: dict[str, str]) -> str | None:
    if valor_nulo(name):
        return None
    norm = normalizar_texto(name)
    return alias_map.get(norm, norm)


def construir_dim_date(data: DatasetGroup) -> pd.DataFrame:
    fechas: set[pd.Timestamp] = set()

    for col in ["fecha_liquidacion"]:
        if col in data.compras.columns:
            vals = pd.to_datetime(data.compras[col], errors="coerce").dropna()
            fechas.update(vals.tolist())

    for col in ["fecha"]:
        if col in data.contrataciones.columns:
            vals = pd.to_datetime(data.contrataciones[col], errors="coerce").dropna()
            fechas.update(vals.tolist())

    for col in ["fecha_inicio", "fecha_fin"]:
        if col in data.becas.columns:
            vals = pd.to_datetime(data.becas[col], errors="coerce").dropna()
            fechas.update(vals.tolist())

    if "anio_pago" in data.nominas.columns and "mes_pago" in data.nominas.columns:
        for _, row in data.nominas[["anio_pago", "mes_pago"]].dropna().iterrows():
            try:
                dt = pd.Timestamp(year=int(row["anio_pago"]), month=int(row["mes_pago"]), day=1)
            except Exception:
                continue
            fechas.add(dt)

    dim_date = pd.DataFrame({"full_date": sorted(fechas)})
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["date_id"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    return dim_date[["date_id", "full_date", "year", "month", "day"]]


def construir_dim_department(data: DatasetGroup) -> pd.DataFrame:
    rows: list[tuple[str | None, str | None]] = []

    if {"DEPENDENCIA", "UNIDAD"}.issubset(data.nominas.columns):
        for _, row in data.nominas[["DEPENDENCIA", "UNIDAD"]].iterrows():
            dep = None if valor_nulo(row["DEPENDENCIA"]) else normalizar_texto(row["DEPENDENCIA"])
            uni = None if valor_nulo(row["UNIDAD"]) else normalizar_texto(row["UNIDAD"])
            rows.append((dep, uni))

    if "UNIDAD EJECUTORA_NORM" in data.compras.columns:
        for value in data.compras["UNIDAD EJECUTORA_NORM"].tolist():
            rows.append(split_dependencia_unidad(value))

    if "UNIDAD_NORM" in data.contrataciones.columns:
        for value in data.contrataciones["UNIDAD_NORM"].tolist():
            rows.append(split_dependencia_unidad(value))

    dep_df = pd.DataFrame(rows, columns=["dependency_name", "unit_name"])
    dep_df = dep_df.drop_duplicates().reset_index(drop=True)
    return dep_df


def construir_dim_provider(data: DatasetGroup) -> pd.DataFrame:
    rows: list[tuple[str, str | None]] = []

    for _, row in data.compras.iterrows():
        name = normalizar_texto(row.get("PROVEEDOR_NORM", row.get("PROVEEDOR", "")))
        if not name:
            continue
        nit = str(row.get("NIT_NORM", "")).strip() or None
        rows.append((name, nit))

    for _, row in data.contrataciones.iterrows():
        name = normalizar_texto(
            row.get("NOMBRE DEL PROVEEDOR_NORM", row.get("NOMBRE DEL PROVEEDOR", ""))
        )
        if not name:
            continue
        nit = str(row.get("NIT_PROVEEDOR_NORM", "")).strip() or None
        rows.append((name, nit))

    providers = pd.DataFrame(rows, columns=["provider_name", "nit"])
    providers = providers.drop_duplicates().reset_index(drop=True)

    providers = (
        providers.groupby("provider_name", as_index=False)
        .agg({"nit": lambda s: next((x for x in s if not valor_nulo(x)), None)})
        .reset_index(drop=True)
    )
    return providers


def construir_dim_person(data: DatasetGroup, alias_map: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, row in data.votantes.iterrows():
        name = canonical_person_name(row.get("nombre"), alias_map)
        if not name:
            continue
        state_job = None if valor_nulo(row.get("trabajo_estado")) else normalizar_texto(row["trabajo_estado"])
        rows.append(
            {
                "full_name": name,
                "is_voter": True,
                "state_job_voter": state_job,
            }
        )

    for _, row in data.nominas.iterrows():
        source_name = row.get("EMPLEADO_NORM", row.get("EMPLEADO"))
        name = canonical_person_name(source_name, alias_map)
        if not name:
            continue
        rows.append({"full_name": name, "is_voter": False, "state_job_voter": None})

    for _, row in data.becas.iterrows():
        source_name = row.get("BENEFICIARIO_NORM", row.get("BENEFICIARIO"))
        name = canonical_person_name(source_name, alias_map)
        if not name:
            continue
        rows.append({"full_name": name, "is_voter": False, "state_job_voter": None})

    people = pd.DataFrame(rows)
    if people.empty:
        return pd.DataFrame(columns=["full_name", "is_voter", "state_job_voter"])

    def pick_state_job(values: pd.Series) -> str | None:
        for value in values:
            if not valor_nulo(value):
                return str(value)
        return None

    result = (
        people.groupby("full_name", as_index=False)
        .agg(
            {
                "is_voter": "max",
                "state_job_voter": pick_state_job,
            }
        )
        .reset_index(drop=True)
    )
    return result


def build_engine() -> object:
    from sqlalchemy import create_engine

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not db or not user or not password:
        raise ValueError("Define DB_NAME, DB_USER y DB_PASSWORD como variables de entorno.")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def truncar_tablas(conn: object) -> None:
    from sqlalchemy import text

    conn.execute(text("TRUNCATE TABLE fact_scholarships, fact_contracts, fact_purchases, fact_payroll RESTART IDENTITY CASCADE"))
    conn.execute(text("TRUNCATE TABLE dim_person, dim_provider, dim_department, dim_date RESTART IDENTITY CASCADE"))


def crear_lookup(conn: object, table: str, key_cols: list[str], id_col: str) -> dict[tuple, int]:
    from sqlalchemy import text

    cols = ", ".join([id_col] + key_cols)
    rows = conn.execute(text(f"SELECT {cols} FROM {table}")).mappings()
    lookup: dict[tuple, int] = {}
    for row in rows:
        key = tuple(row[col] for col in key_cols)
        lookup[key] = row[id_col]
    return lookup


def date_id_from_date(value: object) -> int | None:
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return int(dt.strftime("%Y%m%d"))


def build_fact_payroll(data: DatasetGroup, lookups: dict[str, dict], alias_map: dict[str, str]) -> pd.DataFrame:
    rows = []
    for _, row in data.nominas.iterrows():
        anio = row.get("anio_pago")
        mes = row.get("mes_pago")
        if valor_nulo(anio) or valor_nulo(mes):
            continue
        try:
            date_id = int(f"{int(float(anio)):04d}{int(float(mes)):02d}01")
        except Exception:
            continue

        person_name = canonical_person_name(row.get("EMPLEADO_NORM", row.get("EMPLEADO")), alias_map)
        if not person_name:
            continue

        dep = None if valor_nulo(row.get("DEPENDENCIA")) else normalizar_texto(row.get("DEPENDENCIA"))
        uni = None if valor_nulo(row.get("UNIDAD")) else normalizar_texto(row.get("UNIDAD"))

        person_id = lookups["person"].get((person_name,))
        dept_id = lookups["department"].get((dep, uni))

        if person_id is None or dept_id is None or date_id not in lookups["date"]:
            continue

        rows.append(
            {
                "person_id": person_id,
                "department_id": dept_id,
                "date_id": date_id,
                "renglon": str(row.get("RENGLON", "")).strip() or None,
                "base_salary": pd.to_numeric(row.get("SUELDO BASE"), errors="coerce"),
                "nominal_salary": pd.to_numeric(row.get("NOMINAL"), errors="coerce"),
                "liquid_salary": pd.to_numeric(row.get("LIQUIDO"), errors="coerce"),
            }
        )

    return pd.DataFrame(rows)


def build_fact_purchases(data: DatasetGroup, lookups: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for _, row in data.compras.iterrows():
        date_id = date_id_from_date(row.get("fecha_liquidacion"))
        if date_id is None or date_id not in lookups["date"]:
            continue

        provider_name = normalizar_texto(row.get("PROVEEDOR_NORM", row.get("PROVEEDOR", "")))
        provider_id = lookups["provider"].get((provider_name,))
        if provider_id is None:
            continue

        dep, uni = split_dependencia_unidad(row.get("UNIDAD EJECUTORA_NORM", row.get("UNIDAD EJECUTORA")))
        dept_id = lookups["department"].get((dep, uni))
        if dept_id is None:
            continue

        rows.append(
            {
                "provider_id": provider_id,
                "department_id": dept_id,
                "date_id": date_id,
                "description": row.get("DESCRIPCION DE LA COMPRA"),
                "quantity": pd.to_numeric(row.get("CANTIDAD"), errors="coerce"),
                "unit_price": pd.to_numeric(row.get("PRECIO UNITARIO"), errors="coerce"),
                "total_amount": pd.to_numeric(row.get("PRECIO TOTAL"), errors="coerce"),
            }
        )

    return pd.DataFrame(rows)


def build_fact_contracts(data: DatasetGroup, lookups: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for _, row in data.contrataciones.iterrows():
        date_id = date_id_from_date(row.get("fecha"))
        if date_id is None or date_id not in lookups["date"]:
            continue

        provider_name = normalizar_texto(
            row.get("NOMBRE DEL PROVEEDOR_NORM", row.get("NOMBRE DEL PROVEEDOR", ""))
        )
        provider_id = lookups["provider"].get((provider_name,))
        if provider_id is None:
            continue

        dep, uni = split_dependencia_unidad(row.get("UNIDAD_NORM", row.get("UNIDAD")))
        dept_id = lookups["department"].get((dep, uni))
        if dept_id is None:
            continue

        rows.append(
            {
                "provider_id": provider_id,
                "department_id": dept_id,
                "date_id": date_id,
                "description": row.get("DESCRIPCION DEL GASTO"),
                "renglon": str(row.get("RENGLON PRESUPUESTARIO", "")).strip() or None,
                "units": pd.to_numeric(row.get("UNIDADES"), errors="coerce"),
                "total_amount": pd.to_numeric(row.get("MONTO TOTAL"), errors="coerce"),
            }
        )

    return pd.DataFrame(rows)


def build_fact_scholarships(data: DatasetGroup, lookups: dict[str, dict], alias_map: dict[str, str]) -> pd.DataFrame:
    rows = []
    for _, row in data.becas.iterrows():
        person_name = canonical_person_name(row.get("BENEFICIARIO_NORM", row.get("BENEFICIARIO")), alias_map)
        person_id = lookups["person"].get((person_name,)) if person_name else None
        if person_id is None:
            continue

        start_id = date_id_from_date(row.get("fecha_inicio"))
        end_id = date_id_from_date(row.get("fecha_fin"))
        if start_id is None or end_id is None:
            continue
        if start_id not in lookups["date"] or end_id not in lookups["date"]:
            continue

        rows.append(
            {
                "person_id": person_id,
                "date_start_id": start_id,
                "date_end_id": end_id,
                "scholarship_type": row.get("TIPO_BECA_NORM", row.get("TIPO DE BECA")),
                "amount": pd.to_numeric(row.get("MONTO"), errors="coerce"),
            }
        )

    return pd.DataFrame(rows)


def run_etl(full_refresh: bool) -> None:
    data = cargar_datasets()
    alias_map = cargar_alias_personas()

    dim_date = construir_dim_date(data)
    dim_department = construir_dim_department(data)
    dim_provider = construir_dim_provider(data)
    dim_person = construir_dim_person(data, alias_map)

    engine = build_engine()

    with engine.begin() as conn:
        if full_refresh:
            truncar_tablas(conn)

        dim_date.to_sql("dim_date", conn, if_exists="append", index=False, method="multi", chunksize=5000)
        dim_department.to_sql(
            "dim_department", conn, if_exists="append", index=False, method="multi", chunksize=5000
        )
        dim_provider.to_sql("dim_provider", conn, if_exists="append", index=False, method="multi", chunksize=5000)
        dim_person.to_sql("dim_person", conn, if_exists="append", index=False, method="multi", chunksize=5000)

        lookups = {
            "date": {k[0]: v for k, v in crear_lookup(conn, "dim_date", ["date_id"], "date_id").items()},
            "department": crear_lookup(
                conn, "dim_department", ["dependency_name", "unit_name"], "department_id"
            ),
            "provider": crear_lookup(conn, "dim_provider", ["provider_name"], "provider_id"),
            "person": crear_lookup(conn, "dim_person", ["full_name"], "person_id"),
        }

        fact_payroll = build_fact_payroll(data, lookups, alias_map)
        fact_purchases = build_fact_purchases(data, lookups)
        fact_contracts = build_fact_contracts(data, lookups)
        fact_scholarships = build_fact_scholarships(data, lookups, alias_map)

        if not fact_payroll.empty:
            fact_payroll.to_sql(
                "fact_payroll", conn, if_exists="append", index=False, method="multi", chunksize=5000
            )
        if not fact_purchases.empty:
            fact_purchases.to_sql(
                "fact_purchases", conn, if_exists="append", index=False, method="multi", chunksize=5000
            )
        if not fact_contracts.empty:
            fact_contracts.to_sql(
                "fact_contracts", conn, if_exists="append", index=False, method="multi", chunksize=5000
            )
        if not fact_scholarships.empty:
            fact_scholarships.to_sql(
                "fact_scholarships",
                conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=5000,
            )

    print("Carga completada.")
    print(f"dim_date: {len(dim_date)}")
    print(f"dim_department: {len(dim_department)}")
    print(f"dim_provider: {len(dim_provider)}")
    print(f"dim_person: {len(dim_person)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga de datos limpios al esquema estrella en PostgreSQL.")
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Trunca dimensiones y hechos antes de cargar.",
    )
    args = parser.parse_args()
    run_etl(full_refresh=args.full_refresh)


if __name__ == "__main__":
    main()
