import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from include.json_writer import save_videos_to_json
from include.youtube_client import (
    get_channel_id,
    get_playlist_videos,
    get_videos_details,
)


def _get_channel_id(ti):
    _, uploads_playlist_id = get_channel_id(Variable.get("CHANNEL_HANDLE"))
    ti.xcom_push("uploads_playlist_id", uploads_playlist_id)
    return uploads_playlist_id


def _get_playlist_videos(ti):
    uploads_playlist_id = ti.xcom_pull(task_ids="get_channel_id", key="uploads_playlist_id")
    video_ids = get_playlist_videos(uploads_playlist_id)
    ti.xcom_push("video_ids", video_ids)
    return video_ids


def _get_videos_details(ti):
    video_ids = ti.xcom_pull(task_ids="get_playlist_videos", key="video_ids")
    videos = get_videos_details(video_ids)
    ti.xcom_push("videos", videos)
    return videos


def _save_json(ti):
    videos = ti.xcom_pull(task_ids="get_videos_details", key="videos")
    json_filepath = save_videos_to_json(videos)
    ti.xcom_push("json_filepath", json_filepath)
    return json_filepath


with DAG(
    dag_id="youtube_extraction",
    start_date=datetime(2026, 9, 18),
    schedule=None,
    catchup=False,
) as dag:

    get_channel_id_task = PythonOperator(
        task_id="get_channel_id",
        python_callable=_get_channel_id,
    )

    get_playlist_videos_task = PythonOperator(
        task_id="get_playlist_videos",
        python_callable=_get_playlist_videos,
    )

    get_videos_details_task = PythonOperator(
        task_id="get_videos_details",
        python_callable=_get_videos_details,
    )

    save_json_task = PythonOperator(
        task_id="save_json",
        python_callable=_save_json,
    )

    trigger_warehouse_update = TriggerDagRunOperator(
        task_id="trigger_warehouse_update",
        trigger_dag_id="warehouse_update",
        conf={
            "json_filepath": "{{ ti.xcom_pull(task_ids='save_json', key='json_filepath') }}"
        },
    )

    (
        get_channel_id_task
        >> get_playlist_videos_task
        >> get_videos_details_task >> save_json_task>> trigger_warehouse_update
    )