# Superset (Docker)

Este directorio contiene la configuración mínima para ejecutar Apache Superset con Docker Compose.

## 1) Preparación

Desde la raíz del proyecto:

```bash
cp .env.superset.example .env.superset
```

Edita `.env.superset` y define una `SUPERSET_SECRET_KEY` segura.

## 2) Levantar Superset

```bash
docker compose --env-file .env.superset -f docker-compose.superset.yml up -d --build
```

Esta imagen instala `psycopg2-binary` dentro del entorno virtual de Superset (`/app/.venv`) para que la conexión a PostgreSQL funcione también en instalaciones limpias en otra PC.

Interfaz web:

- `http://localhost:8088`

Usuario inicial (según `.env.superset`):

- `SUPERSET_ADMIN_USERNAME`
- `SUPERSET_ADMIN_PASSWORD`

## 3) Conectar con PostgreSQL del proyecto BI

Tu PostgreSQL del DW está expuesto en `localhost:5435` del host.

Como Superset corre en contenedor, dentro del contenedor debes usar `host.docker.internal`.

URI sugerida para crear la conexión en Superset:

```text
postgresql+psycopg2://<db_user>:<db_password>@host.docker.internal:5435/<db_name>
```

### Pasos en UI

1. Inicia sesión en Superset.
2. Ve a **Settings -> Database Connections -> + Database**.
3. Selecciona **PostgreSQL**.
4. Pega la URI y haz **Test Connection**.
5. Guarda la conexión.

## 4) Verificación rápida

Verificar driver PostgreSQL dentro del contenedor:

```bash
docker exec superset_app /app/.venv/bin/python -c "import psycopg2; print(psycopg2.__version__)"
```

En SQL Lab, ejecuta:

```sql
SELECT COUNT(*) FROM dim_person;
SELECT COUNT(*) FROM fact_payroll;
```

## 5) Apagar servicios

```bash
docker compose --env-file .env.superset -f docker-compose.superset.yml down
```
