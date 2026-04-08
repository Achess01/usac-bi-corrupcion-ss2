from __future__ import annotations

from pathlib import Path

from limpiar_becas import limpiar_becas
from limpiar_compras_directas import limpiar_compras_directas
from limpiar_contrataciones_bienes_servicios import (
    limpiar_contrataciones_bienes_servicios,
)
from limpiar_nominas import limpiar_nominas
from limpiar_votantes import limpiar_votantes
from generar_alias_candidatos import generar_alias_candidatos


def main() -> None:
    salida = Path("data/clean")
    salida.mkdir(parents=True, exist_ok=True)

    limpiar_votantes()
    limpiar_compras_directas()
    limpiar_contrataciones_bienes_servicios()
    limpiar_becas()
    limpiar_nominas()
    generar_alias_candidatos()

    print("Limpieza completada. Archivos disponibles en data/clean/.")


if __name__ == "__main__":
    main()
