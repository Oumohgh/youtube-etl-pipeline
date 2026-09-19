from datetime import datetime, timezone

from airflow.providers.postgres.hooks.postgres import PostgresHook

from include.transform import transform_staging_rows

STAGING_COLUMNS = (
    "video_id",
    "title",
    "published_at",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
)


def _ensure_core_table(hook):
    hook.run(
        """
        CREATE TABLE IF NOT EXISTS core (
            video_id VARCHAR(20) PRIMARY KEY,
            title TEXT,
            published_at TIMESTAMP,
            duration_seconds INTEGER,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            updated_at TIMESTAMP
        )
        """
    )


def read_staging_rows():
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_elt")
    rows = hook.get_records(f"SELECT {', '.join(STAGING_COLUMNS)} FROM staging")
    return [dict(zip(STAGING_COLUMNS, row)) for row in rows]


def get_transformed_staging_rows():
    return transform_staging_rows(read_staging_rows())


def sync_core(transformed_videos):
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_elt")
    _ensure_core_table(hook)

    
    hook.run("DELETE FROM core WHERE video_id NOT IN (SELECT video_id FROM staging)")

    for video in transformed_videos:
        hook.run(
            """
            INSERT INTO core (
                video_id, title, published_at, duration_seconds,
                view_count, like_count, comment_count, updated_at
            )
            VALUES (
                %(video_id)s, %(title)s, %(published_at)s, %(duration_seconds)s,
                %(view_count)s, %(like_count)s, %(comment_count)s, %(updated_at)s
            )
            ON CONFLICT (video_id) DO UPDATE SET
                title = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                duration_seconds = EXCLUDED.duration_seconds,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count,
                updated_at = EXCLUDED.updated_at
            """,
            parameters={
                "video_id": video["video_id"],
                "title": video["title"],
                "published_at": video["published_at"],
                "duration_seconds": video["duration_seconds"],
                "view_count": video["view_count"],
                "like_count": video["like_count"],
                "comment_count": video["comment_count"],
                "updated_at": datetime.now(timezone.utc),
            },
        )

    print(f"Core sync: {len(transformed_videos)} videos upserted")