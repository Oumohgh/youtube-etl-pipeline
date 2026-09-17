from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def get_channel_id():
    print("Getting channel ID...")


def get_playlist_videos():
    print("Getting playlist videos...")


def get_videos_details():
    print("Getting video details...")


def save_ytdata():
    print("Saving YTdata.json...")


with DAG(
    dag_id="youtube_extrac",
    start_date=datetime(2026, 9, 16),
    schedule=None,
    catchup=False,
) as dag:


    get_channel_id_task = PythonOperator(
        task_id="get_channel_id",
        python_callable=get_channel_id,
    )

    get_playlist_videos_task = PythonOperator(
        task_id="get_playlist_videos",
        python_callable=get_playlist_videos,
    )


