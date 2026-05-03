FROM apache/airflow:3.2.1

USER airflow

COPY --chown=airflow:0 pyproject.toml README.md /opt/airflow/app/
COPY --chown=airflow:0 src /opt/airflow/app/src

RUN pip install --no-cache-dir "pypdf>=5.0.0" && \
    pip install --no-cache-dir --no-deps /opt/airflow/app
