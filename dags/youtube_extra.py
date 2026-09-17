
import os
import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from include.get_video_ids import (
    get_channel_id,
    get_playlist_videos,
    get_videos_details,
    save_ytdata,
)


def _get_channel_id():
    handle = os.getenv("CHANNEL_HANDLE")

    if not handle:
        raise ValueError(
            "CHANNEL_HANDLE non défini dans l'environnement (.env)"
        )

    channel_id, uploads_playlist_id = get_channel_id(handle)

    print(f"Channel found: {channel_id}")

    return uploads_playlist_id


def _get_playlist_videos(uploads_playlist_id):
    return get_playlist_videos(uploads_playlist_id)


def _get_videos_details(video_ids):
    return get_videos_details(video_ids)


def _save_ytdata(videos):
    return save_ytdata(videos)


with DAG(
    dag_id="youtube_extraction",
    start_date=datetime(2026, 9, 16),
    schedule="@daily",
    catchup=False,
) as dag:

    get_channel_id_task = PythonOperator(
        task_id="get_channel_id",
        python_callable=_get_channel_id,
    )

    get_playlist_videos_task = PythonOperator(
        task_id="get_playlist_videos",
        python_callable=_get_playlist_videos,
        op_kwargs={
            "uploads_playlist_id": get_channel_id_task.output,
        },
    )

    get_videos_details_task = PythonOperator(
        task_id="get_videos_details",
        python_callable=_get_videos_details,
        op_kwargs={
            "video_ids": get_playlist_videos_task.output,
        },
    )

    save_ytdata_task = PythonOperator(
        task_id="save_ytdata",
        python_callable=_save_ytdata,
        op_kwargs={
            "videos": get_videos_details_task.output,
        },
    )

    trigger_elt_dag_task = TriggerDagRunOperator(
        task_id="trigger_elt_dag",
        trigger_dag_id="youtube_elt",
        conf={
            "json_filepath": "{{ ti.xcom_pull(task_ids='save_ytdata') }}"
        },
    )

    (
        get_channel_id_task
        >> get_playlist_videos_task
        >> get_videos_details_task
        >> save_ytdata_task
        >> trigger_elt_dag_task
    )

