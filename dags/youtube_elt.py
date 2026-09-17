import os
import sys
from datetime import date, datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from include.load_to_core import sync_core
from include.load_to_staging import load_json_to_staging
from include.transform_data import transform_staging


def _load_staging(ti, dag_run):
    data_dir = os.getenv("DATA_DIR", "data")
    default_file = os.path.join(data_dir, f"YTdata{date.today()}.json")
    json_filepath = (dag_run.conf or {}).get("json_filepath", default_file)

    load_json_to_staging(json_filepath)
    ti.xcom_push("source_filepath", json_filepath)
    return json_filepath


def _transform(ti):
    clean_filepath = transform_staging()
    ti.xcom_push("clean_filepath", clean_filepath)
    return clean_filepath


def _load_core(ti):
    clean_filepath = ti.xcom_pull(task_ids="transform", key="clean_filepath")
    sync_core(clean_filepath)


with DAG(
    dag_id="youtube_elt",
    start_date=datetime(2026, 9, 16),
    schedule="@daily",
    catchup=False,
) as dag:

    load_staging_task = PythonOperator(
        task_id="load_staging",
        python_callable=_load_staging,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=_transform,
    )

    load_core_task = PythonOperator(
        task_id="load_core",
        python_callable=_load_core,
    )

    load_staging_task >> transform_task >> load_core_task