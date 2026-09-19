import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from include.core_loader import get_transformed_staging_rows, sync_core
from include.json_writer import read_json
from include.staging_loader import sync_staging


def _sync_staging(dag_run):
    json_filepath = dag_run.conf.get("json_filepath")
    if not json_filepath:
        raise ValueError(
            "json_filepath manquant dans dag_run.conf — "
            "ce DAG doit être déclenché par youtube_extraction, pas manuellement sans conf."
        )
    sync_staging(read_json(json_filepath))


def _transform_data(ti):
    transformed_videos = get_transformed_staging_rows()
    ti.xcom_push("transformed_videos", transformed_videos)
    return transformed_videos


def _sync_core(ti):
    transformed_videos = ti.xcom_pull(task_ids="transform_data", key="transformed_videos")
    sync_core(transformed_videos)


with DAG(
    dag_id="warehouse_update",
    start_date=datetime(2026, 9, 12),
    schedule=None,
    catchup=False,
) as dag:

    sync_staging_task = PythonOperator(
        task_id="sync_staging",
        python_callable=_sync_staging,
    )

    transform_data_task = PythonOperator(
        task_id="transform_data",
        python_callable=_transform_data,
    )

    sync_core_task = PythonOperator(
        task_id="sync_core",
        python_callable=_sync_core,
    )

    sync_staging_task >> transform_data_task >> sync_core_task
