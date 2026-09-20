from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = "sqlite:///./darsio.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread" : False}

)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Lightweight forward-compatible migration for SQLite. `create_all` does not
# alter existing tables, so we add any missing nullable columns manually. This
# preserves existing users while making new optional columns available.
_USER_COLUMN_ADDITIONS: list[tuple[str, str]] = [
    ("first_name", "VARCHAR(80)"),
    ("last_name", "VARCHAR(80)"),
    ("education_level", "VARCHAR(80)"),
    ("field_of_study", "VARCHAR(120)"),
    ("activity_field", "VARCHAR(120)"),
]


def ensure_user_columns() -> None:
    """Add newly introduced optional columns to the existing `users` table."""
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("users")}

    with engine.begin() as conn:
        for name, ddl in _USER_COLUMN_ADDITIONS:
            if name not in existing:
                conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN {name} {ddl}")
                )

        if "allow_data_usage" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN "
                    "allow_data_usage BOOLEAN NOT NULL DEFAULT 0"
                )
            )