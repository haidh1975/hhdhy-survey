import os
import logging
from sqlalchemy import create_engine, MetaData, text
try:
    from sqlalchemy.orm import declarative_base  # SQLAlchemy 2.0+
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base  # SQLAlchemy <2.0
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration — hỗ trợ PostgreSQL (production) và SQLite (local dev)
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Fallback sang SQLite cho môi trường local
    _db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(_db_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(_db_dir, 'survey_app.db')}"
    logger.warning(f"DATABASE_URL không được đặt, dùng SQLite: {DATABASE_URL}")

_is_sqlite = DATABASE_URL.startswith("sqlite")

# Create engine với cấu hình phù hợp từng loại DB
if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )

# Create metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Get database session with automatic cleanup
    """
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """
    Initialize database and create all tables
    """
    try:
        # Import models to register them with Base
        from utils.models import User, Survey, Response
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create default admin user if not exists
        from utils.db_utils import create_default_admin
        create_default_admin()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def test_connection():
    """
    Test database connection
    """
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def execute_raw_sql(sql_query: str, params: dict = None):
    """
    Execute raw SQL query (for admin/debugging purposes)
    """
    try:
        session = SessionLocal()
        result = session.execute(text(sql_query), params or {})
        session.commit()
        
        # For SELECT queries, fetch results
        if sql_query.strip().upper().startswith('SELECT'):
            return result.fetchall()
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        session.rollback()
        session.close()
        raise

# Database health check
def check_database_health():
    """
    Check database health and return status (tương thích cả PostgreSQL và SQLite)
    """
    try:
        session = SessionLocal()

        if _is_sqlite:
            result = session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
        else:
            result = session.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ))
        table_count = result.scalar()

        session.close()

        return {
            "status": "healthy",
            "tables_count": table_count,
            "connection": "active",
            "db_type": "SQLite" if _is_sqlite else "PostgreSQL"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }