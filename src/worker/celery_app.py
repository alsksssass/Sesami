"""
Celery 애플리케이션 설정
"""
import os
from celery import Celery

# 환경 변수 로드
QUEUE_BROKER_URL = os.environ.get('QUEUE_BROKER_URL', 'redis://queue:6379/0')
DATABASE_URL = os.environ.get('DATABASE_URL')

# Celery 앱 생성
celery_app = Celery(
    'worker',
    broker=QUEUE_BROKER_URL,
    backend=QUEUE_BROKER_URL,
    include=['tasks']  # tasks 모듈 자동 로드 (상대 경로)
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분 타임아웃
    task_soft_time_limit=25 * 60,  # 25분 소프트 타임아웃
    worker_prefetch_multiplier=1,  # 한 번에 하나의 작업만 가져오기
    worker_max_tasks_per_child=50,  # 50개 작업 후 워커 재시작 (메모리 누수 방지)
)

if __name__ == '__main__':
    celery_app.start()
