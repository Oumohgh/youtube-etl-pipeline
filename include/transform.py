import re
from datetime import datetime, timezone

ISO_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?"
)

VIRAL_THRESHOLD = 1_000_000
HIGH_THRESHOLD = 100_000
MEDIUM_THRESHOLD = 10_000


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


def _to_datetime(value):
    """Convertit une date ISO 8601 (ex: 2023-01-15T10:00:00Z) en datetime UTC."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def transform_staging_rows(rows):
    """Transforme les lignes brutes de staging en lignes typees pour core."""
    transformed = []
    for row in rows:
        view_count = to_int(row.get("view_count"))
        like_count = to_int(row.get("like_count"))
        comment_count = to_int(row.get("comment_count"))
        published_at = _to_datetime(row.get("published_at"))

        if view_count > 0:
            engagement_rate = round((like_count + comment_count) / view_count * 100, 2)
        else:
            engagement_rate = None

        transformed.append(
            {
                "video_id": row.get("video_id"),
                "title": row.get("title") or "Untitled",
                "published_at": published_at,
                "duration_seconds": duration_to_seconds(row.get("duration")),
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "engagement_rate": engagement_rate,
                # jours depuis la publication : mesure la fraicheur du contenu,
                # utile pour suivre la vitesse de croissance des videos.
                "days_since_publish": (
                    (datetime.now(timezone.utc) - published_at).days if published_at else None
                ),
                "popularity_level": classify_popularity(view_count),
            }
        )
    return transformed