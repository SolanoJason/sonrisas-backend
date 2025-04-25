from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine, URL
from app.config import settings

url = URL.create(
    drivername=settings.DB_DRIVER,
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME
)

engine = create_engine(url, pool_size=5, max_overflow=10, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=True, autoflush=False)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()