import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from include.schema import core_videos, get_engine, init_schema

COMPARED_COLUMNS = (
    "title",
    "published_at",
    "duration_seconds",
    "view_count",
    "like_count",
    "comment_count",
    "engagement_rate",
    "days_since_publish",
    "popularity_level",
)


def _to_timestamp(value):
    """Normalise une valeur de date en datetime UTC (garde les comparaisons fiables)."""
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _values_for_core(record):
    values = {column: record.get(column) for column in COMPARED_COLUMNS}
    if values["published_at"] is not None:
        values["published_at"] = _to_timestamp(values["published_at"])
    return values


def sync_core(clean_filepath):
    """Synchronise la table Core avec les donnees transformees (INSERT / UPDATE / DELETE)."""
    engine = get_engine()
    init_schema()

    with open(clean_filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    with engine.begin() as conn:
        existing = {r["video_id"]: r for r in conn.execute(select(core_videos)).mappings()}
        source_ids = {record["video_id"] for record in records}

        deleted_ids = [video_id for video_id in existing if video_id not in source_ids]
        if deleted_ids:
            conn.execute(
                core_videos.delete().where(core_videos.c.video_id.in_(deleted_ids))
            )

        inserted = updated = unchanged = 0
        now = datetime.now(timezone.utc)

        for record in records:
            video_id = record["video_id"]
            values = _values_for_core(record)

            if video_id not in existing:
                conn.execute(
                    core_videos.insert().values(video_id=video_id, updated_at=now, **values)
                )
                inserted += 1
                continue

            current = existing[video_id]
            if any(current[column] != values[column] for column in COMPARED_COLUMNS):
                conn.execute(
                    core_videos.update()
                    .where(core_videos.c.video_id == video_id)
                    .values(updated_at=now, **values)
                )
                updated += 1
            else:
                unchanged += 1

        print(
            f"Core sync : {inserted} inserted, {updated} updated, "
            f"{len(deleted_ids)} deleted, {unchanged} unchanged"
        )
        return {
            "inserted": inserted,
            "updated": updated,
            "deleted": len(deleted_ids),
            "unchanged": unchanged,
        }


if __name__ == "__main__":
    import os
    from datetime import date

    default_file = os.path.join(
        os.getenv("DATA_DIR", "data"), f"YTdata{date.today()}_clean.json"
    )
    print(sync_core(sys.argv[1] if len(sys.argv) > 1 else default_file))