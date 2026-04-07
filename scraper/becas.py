from io import StringIO
import os

import pandas as pd
import requests


def scrape_becas():
    url = "https://www3.usac.edu.gt/cip/muestra15.php"
    list_of_years = [2022, 2023, 2024, 2025, 2025]

    for year in list_of_years:
        datos_formulario = {
            "anyo": str(year),
            "enviar": "Consultar",
        }
        cabeceras = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        print(f"Obteniendo datos de becas para el año {year}...")
        respuesta = requests.post(url, data=datos_formulario, headers=cabeceras)

        print("Obteniendo la tabla...")
        tablas = pd.read_html(StringIO(respuesta.text), header=0)
        df_becas = tablas[0]

        print(f"Guardando archivo para el año {year}...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(script_dir, "../data", "raw")
        csv_file = os.path.join(data_file, f"becas_usac_{year}.csv")

        df_becas.to_csv(csv_file, sep=";", index=False)

    print(f"Finalizado el proceso de scraping de becas para los años {list_of_years}.")


if __name__ == "__main__":
    try:
        scrape_becas()
    except Exception as e:
        print(f"Ocurrió un error durante el proceso de scraping de becas: {e}")
