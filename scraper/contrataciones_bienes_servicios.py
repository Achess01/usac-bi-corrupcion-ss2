from io import StringIO
import os

import pandas as pd
import requests


def scrape_contrataciones_bienes_servicios():
    url = "https://www3.usac.edu.gt/cip/muestra11.php"
    list_of_years = [2023, 2024, 2025, 2026]

    for year in list_of_years:
        datos_formulario = {
            "anyo": str(year),
            "enviar": "Consultar",
        }
        cabeceras = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        print(f"Obteniendo datos de contrataciones para el año {year}...")
        respuesta = requests.post(url, data=datos_formulario, headers=cabeceras)

        print("Obteniendo la tabla...")
        tablas = pd.read_html(StringIO(respuesta.text), header=0)
        df_contrataciones = tablas[0]

        print(f"Guardando archivo para el año {year}...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(script_dir, "../data", "raw")
        csv_file = os.path.join(
            data_file,
            f"contrataciones_bienes_servicios_usac_{year}.csv",
        )

        df_contrataciones.to_csv(csv_file, sep=";", index=False)

    print(
        "Finalizado el proceso de scraping de contrataciones de bienes y "
        f"servicios para los años {list_of_years}."
    )


if __name__ == "__main__":
    try:
        scrape_contrataciones_bienes_servicios()
    except Exception as e:
        print(
            "Ocurrió un error durante el proceso de scraping de "
            f"contrataciones: {e}"
        )
