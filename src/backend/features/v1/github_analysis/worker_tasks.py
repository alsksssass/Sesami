"""
Celery 워커와 통신하기 위한 태스크 함수들
실제 무거운 작업은 별도의 worker 컨테이너에서 실행됩니다.
"""
import os
from celery import Celery
from common.encryption import TokenEncryption

# Celery 앱 연결 (백엔드에서 워커로 작업 전송용)
QUEUE_BROKER_URL = os.environ.get('QUEUE_BROKER_URL', 'redis://queue:6379/0')

celery_app = Celery(
    'backend_tasks',
    broker=QUEUE_BROKER_URL,
    backend=QUEUE_BROKER_URL
)


def enqueue_analysis_task(user_id: int, repo_url: str, encrypted_github_token: str = None):
    """
    분석 작업을 Celery 큐에 등록

    Args:
        user_id: 사용자 ID
        repo_url: GitHub 저장소 URL
        encrypted_github_token: 암호화된 GitHub 토큰 (선택사항)

    Returns:
        Celery AsyncResult 객체
    """
    # 암호화된 토큰을 복호화하여 워커에 전달
    github_token = None
    if encrypted_github_token:
        github_token = TokenEncryption.decrypt(encrypted_github_token)

    # Celery 워커의 analyze_repo_task 호출
    task = celery_app.send_task(
        'analyze_repo_task',  # worker/tasks.py의 태스크 이름
        args=[str(user_id), repo_url, github_token],
        queue='default'
    )

    print(f"✅ 작업 큐에 등록: {task.id} - {repo_url}")
    return task


def get_task_status(task_id: str):
    """
    작업 상태 조회

    Args:
        task_id: Celery 작업 ID

    Returns:
        작업 상태 딕셔너리
    """
    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.ready() else None,
        "info": result.info
    }


def test_celery_connection():
    """Celery 연결 테스트"""
    try:
        task = celery_app.send_task('test_task', args=['Hello from backend!'])
        print(f"✅ Celery 연결 성공: {task.id}")
        return True
    except Exception as e:
        print(f"❌ Celery 연결 실패: {e}")
        return False
