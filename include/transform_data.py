import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from include.schema import get_engine, init_schema, staging_videos

VIRAL_THRESHOLD = 1_000_000
HIGH_THRESHOLD = 100_000
MEDIUM_THRESHOLD = 10_000

ISO_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?"
)


def duration_to_seconds(iso):
    """Convertit une duree au format ISO 8601 (ex: PT1H2M3S) en secondes."""
    if not iso:
        return 0

    match = ISO_DURATION_RE.fullmatch(iso.strip())
    if not match:
        return 0

    days = float(match.group("days") or 0)
    hours = float(match.group("hours") or 0)
    minutes = float(match.group("minutes") or 0)
    seconds = float(match.group("seconds") or 0)

    return int(days * 86400 + hours * 3600 + minutes * 60 + seconds)


def to_int(value, default=0):
    """Convertit une valeur en entier, en appliquant une valeur par defaut si elle est absente."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def classify_popularity(view_count):
    """
    Classe une video selon son audience (regles definies par le projet).

    Seuils justifies : "viral" pour plus d'1 million de vues correspond aux
    videos ayant depasse un seuil de visibilite nationale ; "high" a partir de
    100 000 vues ; "medium" a partir de 10 000 vues ; "low" en dessous.
    Ces categories permettent des analyses de performance par segment.
    """
    if view_count >= VIRAL_THRESHOLD:
        return "viral"
    if view_count >= HIGH_THRESHOLD:
        return "high"
    if view_count >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def transform_dataframe(df):
    """Applique les transformations Staging -> Core (types, dates, durees, metriques derivees)."""
    data = df.copy()

    data["published_at"] = pd.to_datetime(data["published_at"], errors="coerce", utc=True)

    data["duration_seconds"] = data["duration"].map(duration_to_seconds)

    data["view_count"] = data["view_count"].map(to_int)
    data["like_count"] = data["like_count"].map(to_int)
    data["comment_count"] = data["comment_count"].map(to_int)

    data["title"] = data["title"].fillna("").astype(str).str.replace("nan", "", regex=False)
    data.loc[data["title"].eq(""), "title"] = "Untitled"

    safe_views = data["view_count"].replace(0, float("nan"))
    data["engagement_rate"] = (
        ((data["like_count"] + data["comment_count"]) / safe_views) * 100
    ).round(2)

    now = pd.Timestamp.now(tz="UTC")
    data["days_since_publish"] = (now - data["published_at"]).dt.days

    data["popularity_level"] = data["view_count"].map(classify_popularity)

    return data


def transform_staging(clean_filepath=None):
    """Lit la table Staging, applique les transformations et genere le JSON des donnees propres."""
    engine = get_engine()
    init_schema()

    with engine.connect() as conn:
        rows = conn.execute(staging_videos.select()).mappings().all()
    df = pd.DataFrame(rows)
    transformed = transform_dataframe(df)

    if clean_filepath is None:
        data_dir = os.getenv("DATA_DIR", "data")
        os.makedirs(data_dir, exist_ok=True)
        clean_filepath = os.path.join(data_dir, f"YTdata{date.today()}_clean.json")

    records = []
    for record in transformed.to_dict(orient="records"):
        clean_record = {}
        for key, value in record.items():
            if pd.isna(value):
                clean_record[key] = None
            elif hasattr(value, "isoformat"):
                clean_record[key] = value.isoformat()
            elif hasattr(value, "item"):
                clean_record[key] = value.item()
            else:
                clean_record[key] = value
        records.append(clean_record)

    with open(clean_filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

    print(f"Transformed {len(records)} videos -> {clean_filepath}")
    return clean_filepath


if __name__ == "__main__":
    print(transform_staging())