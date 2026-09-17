import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.dialects.postgresql import insert

from include.schema import get_engine, init_schema, staging_videos

UPSERT_COLUMNS = (
    "title",
    "published_at",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
)


def load_json_to_staging(filepath=None):
    if filepath is None:
        data_dir = os.getenv("DATA_DIR", "data")
        filepath = os.path.join(data_dir, f"YTdata{date.today()}.json")

    engine = get_engine()
    init_schema()

    with open(filepath, "r", encoding="utf-8") as f:
        videos = json.load(f)

    with engine.begin() as conn:
        for video in videos:
            stmt = insert(staging_videos).values(
                video_id=video["videoId"],
                title=video.get("title"),
                published_at=video.get("publishedAt"),
                duration=video.get("duration"),
                view_count=video.get("viewCount"),
                like_count=video.get("likeCount"),
                comment_count=video.get("commentCount"),
                loaded_at=datetime.utcnow(),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={column: stmt.excluded[column] for column in UPSERT_COLUMNS}
                | {"loaded_at": stmt.excluded.loaded_at},
            )
            conn.execute(stmt)

        source_ids = {video["videoId"] for video in videos}
        if source_ids:
            conn.execute(staging_videos.delete().where(staging_videos.c.video_id.notin_(source_ids)))

    print(f"Loaded {len(videos)} videos into staging")
    return filepath