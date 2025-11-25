"""
Alembic 환경 설정
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Backend 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Config 및 모델 import
from config import settings
from common.database import Base

# Shared 모델 import (자동 테이블 감지)
from shared.models import Analysis, AnalysisState
from shared.graph_models import GraphSnapshot, VectorIndex

# Feature 모델 import
from features.v1.auth.models import User
# github_analysis/models.py는 shared에서 re-export만 하므로 명시적 import 불필요

# Alembic Config 객체
config = context.config

# Python logging 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata 객체 (마이그레이션 대상)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    'offline' 모드로 마이그레이션 실행
    SQL 스크립트만 생성, 실제 DB 연결 없음
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    'online' 모드로 마이그레이션 실행
    실제 DB에 연결하여 마이그레이션 적용
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
