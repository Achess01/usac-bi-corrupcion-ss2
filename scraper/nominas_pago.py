from io import StringIO
import os

import pandas as pd
import requests


def scrape_nominas_pago():
    url = "https://www3.usac.edu.gt/cip/muestra4tb.php"
    list_of_years = [2022, 2023, 2024, 2025, 2026]
    list_of_months = list(range(1, 13))

    for year in list_of_years:
        for month in list_of_months:
            datos_formulario = {
                "tipo": "1",
                "mes": str(month),
                "anyo": str(year),
            }
            cabeceras = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }

            print(f"Obteniendo nóminas para {year}-{month:02d}...")
            respuesta = requests.post(url, data=datos_formulario, headers=cabeceras)

            print("Obteniendo la tabla...")
            tablas = pd.read_html(StringIO(respuesta.text), header=0)
            df_nominas = tablas[0]

            print(f"Guardando archivo para {year}-{month:02d}...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(script_dir, "../data", "raw")
            csv_file = os.path.join(
                data_file,
                f"nominas_pago_usac_{year}_{month:02d}.csv",
            )

            df_nominas.to_csv(csv_file, sep=";", index=False)

    print("Finalizado el proceso de scraping de nóminas de pago.")


if __name__ == "__main__":
    try:
        scrape_nominas_pago()
    except Exception as e:
        print(f"Ocurrió un error durante el scraping de nóminas: {e}")
