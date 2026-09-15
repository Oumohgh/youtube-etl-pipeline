import json
import os
import 
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "localhost"
DB_PORT = os.getenv("POSTGRES_CONN_PORT", "5432")
DB_NAME = os.getenv("ELT_DATABASE_NAME")
DB_USER = os.getenv("ELT_DATABASE_USERNAME")
DB_PASSWORD = os.getenv("ELT_DATABASE_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = db.create_engine(DATABASE_URL)
connection = engine.connect()

metadata = db.MetaData()
staging_videos = db.Table("staging_videos", metadata, autoload_with=engine)


def load_json_to_staging(filepath="data/YTdata_output.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        videos = json.load(f)

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
        connection.execute(stmt)

    connection.commit()
    print(f"Loaded {len(videos)} videos into staging_videos")


if __name__ == "__main__":
    load_json_to_staging()