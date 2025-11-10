from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class DatabaseManager:
    """
    데이터베이스 연결 관리 싱글톤 클래스

    Usage:
        # 의존성 주입 방식 (FastAPI)
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

        # 직접 사용 방식
        with DatabaseManager.session() as db:
            users = db.query(User).all()
    """

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """데이터베이스 엔진 초기화"""
        if self._engine is None:
            # 연결 풀 설정
            self._engine = create_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=10,              # 연결 풀 크기
                max_overflow=20,           # 최대 오버플로우
                pool_pre_ping=True,        # 연결 유효성 체크
                pool_recycle=3600,         # 1시간마다 연결 재사용
                echo=False,                # SQL 로깅 (개발시 True)
            )

            # 세션 팩토리 생성
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )

            # 연결 이벤트 리스너
            @event.listens_for(self._engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                logger.info("✅ Database connection established")

            @event.listens_for(self._engine, "close")
            def receive_close(dbapi_conn, connection_record):
                logger.info("❌ Database connection closed")

            logger.info(f"🗄️  Database engine initialized: {settings.DATABASE_URL.split('@')[-1]}")

    @property
    def engine(self):
        """SQLAlchemy 엔진 반환"""
        return self._engine

    @property
    def session_factory(self):
        """세션 팩토리 반환"""
        return self._session_factory

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        컨텍스트 매니저로 세션 생성

        Usage:
            with DatabaseManager().session() as db:
                user = db.query(User).first()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def create_all_tables(self):
        """모든 테이블 생성"""
        Base.metadata.create_all(bind=self._engine)
        logger.info("✅ All tables created")

    def drop_all_tables(self):
        """모든 테이블 삭제 (주의!)"""
        Base.metadata.drop_all(bind=self._engine)
        logger.warning("⚠️  All tables dropped")

    def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            with self.session() as db:
                db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# 싱글톤 인스턴스
db_manager = DatabaseManager()


# FastAPI 의존성 주입용 함수
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입용 데이터베이스 세션

    Usage:
        @router.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = db_manager.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
