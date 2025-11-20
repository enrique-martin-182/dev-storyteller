import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create data directory if it doesn't exist
if not os.path.exists('./data'):
    os.makedirs('./data')

# SQLAlchemy database URL
# Use DATABASE_URL environment variable for PostgreSQL, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    connect_args = {} # connect_args={"check_same_thread": False} is specific to SQLite
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sql_app.db"  # Use SQLite for simplicity for now
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_engine():
    return engine

def init_db(engine_to_use=None):
    global engine, SessionLocal
    if engine_to_use:
        engine = engine_to_use
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
