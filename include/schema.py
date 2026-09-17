import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    text,
)

load_dotenv()


def get_engine():
    host = os.getenv("POSTGRES_CONN_HOST", "localhost")
    port = os.getenv("POSTGRES_CONN_PORT", "5432")
    user = os.getenv("ELT_DATABASE_USERNAME")
    password = os.getenv("ELT_DATABASE_PASSWORD")
    database = os.getenv("ELT_DATABASE_NAME")
    url = f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"
    return create_engine(url, pool_pre_ping=True)


metadata = MetaData()

staging_videos = Table(
    "staging",
    metadata,
    Column("video_id", String(20), primary_key=True),
    Column("title", Text),
    Column("published_at", String(30)),
    Column("duration", String(30)),
    Column("view_count", String(20)),
    Column("like_count", String(20)),
    Column("comment_count", String(20)),
    Column("loaded_at", DateTime),
)

core_videos = Table(
    "core",
    metadata,
    Column("video_id", String(20), primary_key=True),
    Column("title", Text),
    Column("published_at", DateTime),
    Column("duration_seconds", Integer),
    Column("view_count", BigInteger),
    Column("like_count", BigInteger),
    Column("comment_count", BigInteger),
    Column("engagement_rate", Float),
    Column("days_since_publish", Integer),
    Column("popularity_level", String(20)),
    Column("updated_at", DateTime),
)


def init_schema():
    """Cree les tables (Staging / Core) si necessaire et repare un ancien schema Core."""
    engine = get_engine()

    if not inspect(engine).has_table("core"):
        metadata.create_all(engine)
        return engine

    expected_types = {column.name: column.type.python_type for column in core_videos.columns}
    for column in inspect(engine).get_columns("core"):
        column_name = column["name"]
        column_type = column["type"]

        if column_name not in expected_types:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS core CASCADE"))
            break

        try:
            db_type = column_type.python_type
        except NotImplementedError:
            continue

        if db_type is not expected_types[column_name]:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS core CASCADE"))
            break

    metadata.create_all(engine)
    return engine