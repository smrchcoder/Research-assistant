from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    def __init__(self):
        self.database_url = settings.database_url
        self.engine = create_engine(
            self.database_url,
            echo=settings.db_echo,
            pool_pre_ping=True,  # Test connections before using
            pool_size=5,
            max_overflow=10
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()
        logger.info("Database configuration initialized successfully")

    def get_db(self):
        """Dependency for getting database sessions"""
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            logger.error(f"Database session error: {e}")
            db.rollback()
            raise
        finally:
            db.close()

db_client = DatabaseConfig()