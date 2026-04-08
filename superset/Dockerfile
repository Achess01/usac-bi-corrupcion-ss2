FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary

COPY superset-init.sh /app/superset-init.sh
COPY superset_config.py /app/pythonpath/superset_config.py
RUN chmod +x /app/superset-init.sh

USER superset
