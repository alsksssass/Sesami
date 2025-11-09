# Worker - GitHub 저장소 분석 엔진

Celery 기반 비동기 작업 처리 워커

## 📁 구조

```
src/worker/
├── celery_app.py         # Celery 앱 설정
├── tasks.py              # 분석 태스크 정의
├── database.py           # DB 모델
├── requirements.txt      # Python 의존성
└── README.md
```

## 🔧 주요 태스크

### 1. `analyze_repo_task`
GitHub 저장소를 클론하고 git blame으로 기여도 분석

**입력**:
- `user_id`: 사용자 ID
- `repo_url`: GitHub 저장소 URL
- `user_github_token`: GitHub 토큰 (선택사항)

**출력**:
```json
{
  "status": "success",
  "repo_url": "https://github.com/user/repo",
  "total_contributors": 5,
  "result": {
    "user1@example.com": 1234,
    "user2@example.com": 567
  }
}
```

### 2. `test_task`
연결 테스트용 간단한 태스크

## 🚀 사용 방법

### 백엔드에서 작업 등록
```python
from features.v1.github_analysis.worker_tasks import enqueue_analysis_task

# 작업 큐에 등록
task = enqueue_analysis_task(
    user_id=1,
    repo_url="https://github.com/torvalds/linux",
    github_token="ghp_xxxxx"  # 선택사항
)

print(f"Task ID: {task.id}")
```

### 작업 상태 조회
```python
from features.v1.github_analysis.worker_tasks import get_task_status

status = get_task_status(task_id)
print(status)
# {
#   "task_id": "abc-123",
#   "status": "PROGRESS",
#   "result": None,
#   "info": {"status": "분석 중... (45%)"}
# }
```

## 🔍 작업 상태

- **PENDING**: 대기 중
- **PROGRESS**: 진행 중
- **SUCCESS**: 완료
- **FAILURE**: 실패

## 📊 모니터링

### Celery Flower (웹 UI)
```bash
# Flower 설치
pip install flower

# 실행
celery -A celery_app flower
# http://localhost:5555
```

### 로그 확인
```bash
# Docker Compose
make logs-worker

# 또는
docker-compose logs -f worker
```

### 워커 상태 확인
```bash
# 컨테이너 접속
make shell-worker

# Celery 상태
celery -A celery_app inspect active
celery -A celery_app inspect stats
```

## ⚙️ 설정

### 환경 변수 (.env)
```bash
DATABASE_URL=postgresql://user:pass@db:5432/dbname
QUEUE_BROKER_URL=redis://queue:6379/0
```

### Celery 설정 (celery_app.py)
```python
celery_app.conf.update(
    task_time_limit=30 * 60,        # 30분 타임아웃
    worker_prefetch_multiplier=1,   # 한 번에 1개 작업
    worker_max_tasks_per_child=50,  # 50개 후 재시작
)
```

## 🐛 트러블슈팅

### Q: 작업이 실행되지 않음
**A**: Redis 연결 확인
```bash
docker-compose logs queue
docker-compose exec queue redis-cli ping
# PONG
```

### Q: 메모리 부족
**A**: `worker_max_tasks_per_child` 값 낮추기

### Q: Git clone 실패
**A**: GitHub 토큰 확인 또는 공개 저장소로 테스트

### Q: DB 연결 오류
**A**: DATABASE_URL 확인 및 DB 컨테이너 상태 확인

## 📈 성능 최적화

### 동시 실행 수 조절
```bash
# docker-compose.yml
command: celery -A celery_app worker --concurrency=4
```

### 메모리 사용 최적화
```python
# Shallow clone (빠른 클론)
Repo.clone_from(url, path, depth=1)

# 큰 저장소는 특정 브랜치만
Repo.clone_from(url, path, branch='main', depth=1)
```

## 🧪 테스트

### 로컬 테스트
```bash
# 워커 실행
celery -A celery_app worker --loglevel=info

# 다른 터미널에서 테스트 태스크 전송
python -c "
from celery_app import celery_app
task = celery_app.send_task('test_task', args=['Hello'])
print(f'Task ID: {task.id}')
"
```

### Docker 환경 테스트
```bash
# 워커 컨테이너 시작
make dev-d

# 백엔드 컨테이너에서 작업 전송
make shell-backend
>>> from features.v1.github_analysis.worker_tasks import test_celery_connection
>>> test_celery_connection()
```

## 📝 작업 흐름

```
1. 백엔드 API: 사용자 요청 받음
   ↓
2. 백엔드: Celery 큐에 작업 등록
   ↓
3. Redis: 작업 대기열에 저장
   ↓
4. Worker: 큐에서 작업 가져옴
   ↓
5. Worker: Git clone → Blame 분석
   ↓
6. Worker: 결과를 DB에 저장
   ↓
7. 백엔드: 결과 조회 API 제공
   ↓
8. 프론트엔드: 결과 표시
```

## 🔐 보안 고려사항

- GitHub 토큰은 암호화하여 저장
- 임시 클론 폴더는 작업 종료 후 즉시 삭제
- 타임아웃 설정으로 무한 실행 방지
- 사용자별 작업 수 제한 (Rate Limiting)

## 🚦 프로덕션 체크리스트

- [ ] Redis 영속성 설정
- [ ] Celery 워커 수 조정
- [ ] 모니터링 (Flower, Sentry)
- [ ] 에러 알림 설정
- [ ] 로그 수집 (ELK, CloudWatch)
- [ ] 백업 전략
- [ ] 스케일링 정책
