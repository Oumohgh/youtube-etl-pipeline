import json
import os
from sqlalchemy import create_engine, MetaData, Table, Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "localhost"
DB_PORT = os.getenv("POSTGRES_CONN_PORT", "5432")
DB_NAME = os.getenv("ELT_DATABASE_NAME")
DB_USER = os.getenv("ELT_DATABASE_USERNAME")
DB_PASSWORD = os.getenv("ELT_DATABASE_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

staging_videos = Table(
    "staging", metadata,
    Column("video_id", String(20), primary_key=True),
    Column("title", Text),
    Column("published_at", String(30)),
    Column("duration", String(20)),
    Column("view_count", String(20)),
    Column("like_count", String(20)),
    Column("comment_count", String(20)),
    Column("loaded_at", TIMESTAMP),
)

core_videos = Table(
    "core", metadata,
    Column("video_id", String(20), primary_key=True),
    Column("title", Text),
    Column("published_at", TIMESTAMP),
    Column("duration_seconds", String(20)),
    Column("view_count", String(20)),
    Column("like_count", String(20)),
    Column("comment_count", String(20)),
    Column("updated_at", TIMESTAMP),
)

metadata.create_all(engine)



from datetime import date
def load_json_to_staging(filepath=None):
    if filepath is None:
        filepath = f"data/YTdata{date.today()}.json"

    with open(filepath, "r", encoding="utf-8") as f:
        videos = json.load(f)

    with engine.connect() as conn:
        for video in videos:
            stmt = insert(staging_videos).values(
                video_id=video["videoId"],
                title=video["title"],
                published_at=video["publishedAt"],
                duration=video["duration"],
                view_count=video["viewCount"],
                like_count=video["likeCount"],
                comment_count=video["commentCount"],
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={
                    "title": stmt.excluded.title,
                    "published_at": stmt.excluded.published_at,
                    "duration": stmt.excluded.duration,
                    "view_count": stmt.excluded.view_count,
                    "like_count": stmt.excluded.like_count,
                    "comment_count": stmt.excluded.comment_count,
                }
            )
            conn.execute(stmt)
        conn.commit()
    print(f"Loaded {len(videos)} videos into staging")

