import re
from datetime import datetime, timezone

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


def _to_datetime(value):
    """Convertit une date ISO 8601 (ex: 2023-01-15T10:00:00Z) en datetime UTC."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def clean_title(title):
    """Nettoie un titre en retirant les espaces superflus."""
    if not title:
        return "Untitled"
    cleaned = title.strip()
    return cleaned or "Untitled"


def transform_staging_rows(rows):
    """Transforme les lignes brutes de staging en lignes typees pour core."""
    transformed = []
    for row in rows:
        transformed.append(
            {
                "video_id": row.get("video_id"),
                "title": clean_title(row.get("title")),
                "published_at": _to_datetime(row.get("published_at")),
                "duration_seconds": duration_to_seconds(row.get("duration")),
                "view_count": to_int(row.get("view_count")),
                "like_count": to_int(row.get("like_count")),
                "comment_count": to_int(row.get("comment_count")),
            }
        )
    return transformed
