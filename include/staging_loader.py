from datetime import datetime

from airflow.providers.postgres.hooks.postgres import PostgresHook


def _ensure_staging_table(hook):
    hook.run(
        """
        CREATE TABLE IF NOT EXISTS staging (
            video_id VARCHAR(20) PRIMARY KEY,
            title TEXT,
            published_at VARCHAR(30),
            duration VARCHAR(20),
            view_count VARCHAR(20),
            like_count VARCHAR(20),
            comment_count VARCHAR(20),
            loaded_at TIMESTAMP
        )
        """
    )


def sync_staging(videos):
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_elt")
    _ensure_staging_table(hook)

    for video in videos:
        hook.run(
            """
            INSERT INTO staging (
                video_id, title, published_at, duration,
                view_count, like_count, comment_count, loaded_at
            )
            VALUES (
                %(video_id)s, %(title)s, %(published_at)s, %(duration)s,
                %(view_count)s, %(like_count)s, %(comment_count)s, %(loaded_at)s
            )
            ON CONFLICT (video_id) DO UPDATE SET
                title = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                duration = EXCLUDED.duration,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count,
                loaded_at = EXCLUDED.loaded_at
            """,
            parameters={
                "video_id": video["videoId"],
                "title": video.get("title"),
                "published_at": video.get("publishedAt"),
                "duration": video.get("duration"),
                "view_count": video.get("viewCount"),
                "like_count": video.get("likeCount"),
                "comment_count": video.get("commentCount"),
                "loaded_at": datetime.utcnow(),
            },
        )

    print(f"Loaded {len(videos)} videos into staging")