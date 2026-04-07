# Análisis de Inteligencia de Negocios: Redes de Clientelismo en la USAC (2021-2026)

**Autor:** Alexander Tzoc Alvarado
**Curso:** Seminario de Sistemas 2
**Stack Tecnológico:** Python (Pandas, Requests) | PostgreSQL | Apache Superset

---

## Introducción
Este proyecto de Inteligencia de Negocios (BI) analiza y cruza datos públicos para identificar posibles patrones de clientelismo, nepotismo y pago de favores durante la administración del rector Walter Mazariegos en la Universidad de San Carlos de Guatemala (USAC). 

A través de la extracción automatizada y consolidación de datos en un Data Warehouse (PostgreSQL), se visualizan (Apache Superset) las relaciones entre los electores del Colegio Electoral Universitario de 2022, las nóminas salariales y las compras directas adjudicadas.

---

## 1. Fase de Descubrimiento

### 1.1 Hipótesis del Negocio
* **Hipótesis A:** Los integrantes del Colegio Electoral Universitario que votaron por la planilla "Innovación y Desarrollo" han recibido incrementos salariales o nuevas contrataciones (Renglón 029) tras la toma de posesión.
* **Hipótesis B:** Existen proveedores de compras directas en Guatecompras vinculados directamente con autoridades o personal administrativo de la USAC.

### 1.2 Mapeo y Origen de Datos
* **Electores (Colegio Electoral 2022):** Datos extraídos de investigaciones periodísticas (Plaza Pública) y actas públicas.
* **Nóminas y Contratos USAC:** Portal de Información Pública de la USAC.
* **Adjudicaciones del Estado:** Portal de Datos Abiertos OCDS de Guatecompras.

### 1.3 Perfilado de Datos y Retos Técnicos
> **Nota Técnica:** Se documenta un hallazgo importante respecto a la transparencia institucional. El portal de la USAC no permite descargas directas ni tiene URLs estáticas. La información está oculta tras un formularios dinámicos. 
* **Solución aplicada:** Se realizó ingeniería inversa a la petición HTTP y se construyó un script en Python (`requests`) que inyecta los *payloads* del formulario (ej. `anyo=2024`) para forzar la respuesta del servidor y extraer las tablas HTML directamente.
* **Calidad de los datos:** .

### 1.4 Scraping de Datos

#### Compras directas
Durante esta fase se revisó el comportamiento de la fuente y se aplicaron mejoras puntuales al flujo actual:

1. **Encabezados desde la tabla origen**
   - Se configuró la lectura de tablas HTML para usar la primera fila como encabezado real.
   - Implementación: `pd.read_html(StringIO(respuesta.text), header=0)`.
   - Resultado: los nombres de columnas en el DataFrame coinciden con los encabezados oficiales del sitio.

2. **Exportación CSV con separador punto y coma**
   - Se actualizó la escritura de CSV para usar `sep=";"`.
   - Implementación: `df_compras.to_csv(csv_file, sep=";", index=False)`.
   - Resultado: mejor compatibilidad con herramientas de hoja de cálculo en configuraciones regionales hispanohablantes.

#### Contrataciones de bienes y servicios
Se incorporó un nuevo script de extracción para el módulo de contrataciones de bienes y servicios de la USAC.

1. **Nuevo endpoint y cobertura de años**
   - Endpoint utilizado: `https://www3.usac.edu.gt/cip/muestra11.php`.
   - Años de extracción: `2023`, `2024`, `2025` y `2026`.
   - Script implementado: `scraper/contrataciones_bienes_servicios.py`.

2. **Lectura de encabezados desde la tabla fuente**
   - Se usa la primera fila HTML como encabezados reales.
   - Implementación: `pd.read_html(StringIO(respuesta.text), header=0)`.

3. **Exportación en CSV con punto y coma**
   - Se mantiene `sep=";"` para compatibilidad regional.
   - Implementación: `df_contrataciones.to_csv(csv_file, sep=";", index=False)`.
   - Nombre de salida por año: `contrataciones_bienes_servicios_usac_{year}.csv` en `data/raw/`.

---

## 2. Fase de Preparación

### 2.1 Proceso de ETL (Extracción, Transformación y Carga)
El proceso de limpieza se realizó utilizando **Python (Pandas)**. Los pasos clave incluyeron:
1. **Homologación de Cadenas:** Conversión de todos los nombres a mayúsculas, eliminación de tildes y espacios en blanco adicionales.
2. **Estructuración de Nombres:** Separación o unión de las columnas de "Nombres" y "Apellidos" para estandarizar las bases del portal del estado vs. el portal de la USAC.

Los scripts de transformación se encuentran en el directorio `/scraper` y los datos resultantes en `/data/clean`.

---

## 3. Fase de Planeación

### 3.1 Arquitectura del Sistema
El flujo de datos obedece a una arquitectura moderna de BI:
* **Extracción/Limpieza:** Python
* **Data Warehouse:** PostgreSQL (Desplegado localmente)
* **Capa Semántica y BI:** Apache Superset

### 3.2 Modelo de Datos
Se implementó un Modelo Estrella para optimizar las consultas analíticas:

* **Tablas de Hechos (Fact Tables):**
  * `fact_nomina`: Contiene los pagos mensuales realizados (salario, bonos, renglón).
  * `fact_compras`: Contiene los montos adjudicados en Guatecompras.
* **Tablas de Dimensiones:**
  * `dim_persona`: Directorio único de empleados y votantes.
  * `dim_proveedor`: Datos de las empresas contratadas.
  * `dim_tiempo`: Meses y años de análisis (2021-2026).

---

## 4. Fase de Construcción

La carga de datos al Data Warehouse en PostgreSQL se realizó mediante el script `load_to_postgres.py` utilizando la librería `SQLAlchemy`.

* Se crearon los esquemas utilizando sentencias DDL puras (ver archivo `/sql/create_schema.sql`).
* Se definieron llaves primarias (`PK`) y llaves foráneas (`FK`) para mantener la integridad referencial y permitir que el Cubo OLAP en Superset pueda cruzar la información sin errores.

---

## 5. Fase de Comunicación

Los resultados se presentan a través de tableros interactivos en **Apache Superset**. 

### 5.1 Hallazgos Principales


### 5.2 Capturas del Dashboard

---

## 6. Fase de Operacionalización

* **Despliegue Futuro:** Esto permite que, en un entorno de producción, el tablero pueda ser restaurado o actualizado utilizando la CLI de Superset
