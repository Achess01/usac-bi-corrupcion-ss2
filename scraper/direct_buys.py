import requests
import pandas as pd
from io import StringIO
import os

def scrape_direct_buys():
    url = "https://www3.usac.edu.gt/cip/muestra22.php"
    list_of_years = [2024, 2025, 2026]

    for year in list_of_years:

        datos_formulario = {
            "anyo": str(year),
            "enviar": "Consultar"
        }
        cabeceras = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        print(f"Obteniendo datos para el año {year}...")
        respuesta = requests.post(url, data=datos_formulario, headers=cabeceras)

        print(f"Obteniendo la tabla...")
        tablas = pd.read_html(StringIO(respuesta.text), header=0)


        df_compras = tablas[0]

        print(f"Guardando archivo para el año {year}...")
        script_dir = os.path.dirname(os.path.abspath(__file__))

        data_file = os.path.join(script_dir, '../data', 'raw')
        csv_file = os.path.join(data_file, f'compras_directas_usac_{year}.csv')

        df_compras.to_csv(csv_file, sep=";", index=False)

    print(f"Finalizado el proceso de scraping para los años {list_of_years}.")

if __name__ == "__main__":
    try:
        scrape_direct_buys()
    except Exception as e:
        print(f"Ocurrió un error durante el proceso de scraping: {e}")
