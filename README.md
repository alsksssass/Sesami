# Sesami - GitHub Contribution Analyzer

## 프로젝트 구조

```
Sesami/
├── docker/                 # Docker 설정 파일
│   ├── frontend/
│   │   └── Dockerfile
│   ├── backend/
│   │   └── Dockerfile
│   ├── worker/
│   │   └── Dockerfile
│   ├── db/
│   │   └── Dockerfile
│   └── queue/
│       └── Dockerfile
├── src/                    # 소스 코드
│   ├── frontend/          # React/Vite 프론트엔드
│   ├── backend/           # FastAPI 백엔드
│   └── worker/            # Celery 워커
├── docker-compose.yml     # Docker Compose 설정
├── .env                   # 환경 변수 (git ignored)
└── README.md
```

## 빠른 시작 (Makefile 사용)

### 기본 명령어
```bash
# 도움말 보기
make help

# 개발 환경 시작
make dev

# 백그라운드로 시작
make dev-d

# 빌드 후 시작
make up

# 캐시 제거 후 완전 재빌드
make fresh

# 로그 보기
make logs

# 중지
make down

# 상태 확인
make status
```

### 주요 명령어

#### 개발
- `make dev` - 개발 환경 시작 (핫 리로딩)
- `make dev-d` - 백그라운드로 시작
- `make stop` - 중지
- `make restart` - 재시작

#### 빌드
- `make build` - 모든 이미지 빌드
- `make rebuild` - 캐시 무효화 후 재빌드
- `make build-frontend` - 프론트엔드만 빌드
- `make build-backend` - 백엔드만 빌드
- `make rebuild-frontend` - 프론트엔드 재빌드
- `make rebuild-backend` - 백엔드 재빌드

#### 실행
- `make up` - 빌드 후 시작
- `make fresh` - 재빌드 후 시작 (완전 초기화)

#### 로그
- `make logs` - 모든 로그
- `make logs-frontend` - 프론트엔드 로그
- `make logs-backend` - 백엔드 로그

#### 클린업
- `make clean` - 모든 리소스 삭제
- `make clean-volumes` - DB 데이터 초기화
- `make prune` - Docker 시스템 정리

#### 개발 도구
- `make shell-backend` - 백엔드 쉘 접속
- `make shell-frontend` - 프론트엔드 쉘 접속
- `make shell-db` - DB 쉘 접속

---

## 수동 실행 (Docker Compose)

### 1. 환경 변수 설정
`.env` 파일이 자동으로 생성되어 있습니다. 필요시 수정하세요.

### 2. Docker Compose 실행
```bash
# 모든 서비스 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down

# 캐시 제거 후 재빌드
docker-compose build --no-cache --pull
docker-compose up
```

## 서비스 접근

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 환경 변수

`.env` 파일에서 다음 변수들을 관리합니다:

### Database
- `POSTGRES_USER`: PostgreSQL 사용자명
- `POSTGRES_PASSWORD`: PostgreSQL 비밀번호
- `POSTGRES_DB`: 데이터베이스 이름
- `DATABASE_URL`: 전체 데이터베이스 연결 URL

### Redis
- `REDIS_HOST`: Redis 호스트
- `REDIS_PORT`: Redis 포트
- `QUEUE_BROKER_URL`: Celery 브로커 URL

### Application
- `FRONTEND_PORT`: 프론트엔드 포트 (기본: 3000)
- `BACKEND_PORT`: 백엔드 포트 (기본: 8000)
- `FRONTEND_URL`: 프론트엔드 URL (CORS 설정용)

@세미 정 

aws batch 를 사용하면 병렬처리를 쉽게 진행(원하는 개수만큼) 가능하기때문에

해당 기능 사용하는것을 베이스로 하여 인프라 설계를 진행합니다.

그렇게 하기위해서 Redis는 추상화 오케스트레이션 로직은 [# worker/run_analysis.py (AWS Batch 실행 스크립트)
import os
import json
import boto3
from analysis.logic import run_full_analysis # 로컬에서 100% 재사용한 핵심 로직

def main():
    # 1. AWS Batch가 주입한 SQS 메시지(작업 내용)를 환경변수에서 읽기
    sqs_message_json = os.environ.get('SQS_MESSAGE_BODY')
    job_data = json.loads(sqs_message_json)
    user_id = job_data['user_id']
    repo_url = job_data['repo_url']

    # 2. (Secrets Manager에서 GitHub 토큰 가져오기)

    try:
        # 3. 핵심 분석 로직 실행 (로컬에서 100% 재활용)
        run_full_analysis(user_id, repo_url)

        # 4. 성공 시 SQS 메시지 삭제 (필수!)
        sqs_receipt_handle = os.environ.get('SQS_RECEIPT_HANDLE')
        sqs = boto3.client('sqs')
        sqs.delete_message(
            QueueUrl=os.environ.get('SQS_QUEUE_URL'),
            ReceiptHandle=sqs_receipt_handle
        )
        print("Job Succeeded.")

    except Exception as e:
        print(f"Job Failed: {e}")
        # 실패 시 메시지를 삭제하지 않으면, SQS가 Dead-Letter-Queue로 보내거나 재시도함
        raise e

if __name__ == "__main__":
    main()

](https://www.notion.so/worker-run_analysis-py-AWS-Batch-import-os-import-json-import-boto3-from-analysis-logic-im-2a24a4f298ed8034be8ae4adf5e6caf8?pvs=21) 방식으로 진행될수있도록 구성해야합니다.

# GitHub 분석기 프로젝트: 로컬 개발 및 AWS 마이그레이션 계획

## 1. 프로젝트 개요

### 1.1. 프로젝트 목표

GitHub OAuth를 통해 사용자의 Access Token을 받아, 해당 사용자가 접근 가능한 모든 저장소(Private 포함)를 분석한다. 분석 항목은 다음과 같다:

- **정량적 기여도:** `git blame`을 기반으로 한 사용자별 코드 라인 기여도 (%).
- **기술 스택 맵:** 저장소 언어 비율, 커밋에 사용된 파일 확장자, 프레임워크 특정 파일(e.g., `package.json`, `pom.xml`, `Dockerfile`) 분석.
- **시계열 분석:** 기간별(주/월) 사용 언어 및 기술 스택 변화 추이.
- **(선택적) 정성적 분석:** SonarQube 등 정적 분석 도구 연동 또는 LLM API를 호출하여 코드 품질 스냅샷 제공.

### 1.2. 핵심 아키텍처: 비동기 작업 처리 (Asynchronous Job Processing)

"요청"과 "처리"를 분리하여 사용자 경험(UX)을 향상시킨다.

1. **Web/API 서버:** 사용자의 인증 및 분석 요청을 접수한다. (즉각 응답)
2. **작업 큐 (Queue):** 분석 요청(Job)을 대기열에 저장한다.
3. **Worker (분석 엔진):** 큐를 감시하며 작업을 가져가, 레포 클론, `git blame`, 코드 분석 등 무겁고 오래 걸리는 작업을 수행한다.
4. **Database:** 분석 결과를 저장하고, API 서버가 이를 조회하여 사용자에게 제공한다.

### 1.3. 핵심 기술 스택 (요약)

| **구분** | **로컬 개발 (Docker Compose)** | **프로덕션 (AWS)** |
| --- | --- | --- |
| **Web/API 서버** | FastAPI (Python) | **Amazon ECS on Fargate** |
| **Worker (분석)** | Celery + Python | **AWS Batch** |
| **작업 큐** | Redis | **Amazon SQS** |
| **데이터베이스** | PostgreSQL | **Amazon RDS (PostgreSQL)** |
| **토큰/보안** | `.env` 파일 | **AWS Secrets Manager** |
| **컨테이너 저장소** | 로컬 빌드 | **Amazon ECR** |
| **인프라 정의** | `docker-compose.yml` | AWS CDK / Terraform |

## 2. 핵심 설계: TaskService 추상화

AWS 마이그레이션 공수를 최소화하기 위해, "작업을 큐에 넣는" 로직을 추상화(Abstraction)합니다. API 서버는 Celery나 SQS의 존재를 몰라야 합니다.

**`interfaces/task_service.py` (가상 인터페이스)**

```
from abc import ABC, abstractmethod

class ITaskService(ABC):
    @abstractmethod
    def submit_analysis_job(self, user_id: str, repo_url: str):
        """사용자의 레포 분석 작업을 큐에 제출합니다."""
        pass

```

**`services/local_task_service.py` (로컬 개발용)**

```
# 'worker.celery_app'는 Celery 앱 인스턴스
from worker.celery_app import analyze_repo_task

class LocalTaskService(ITaskService):
    def submit_analysis_job(self, user_id: str, repo_url: str):
        print(f"[Local] Submitting job for {repo_url} via Celery/Redis...")
        # Celery의 .delay()를 직접 호출
        analyze_repo_task.delay(user_id=user_id, repo_url=repo_url)

```

**`services/aws_task_service.py` (AWS 마이그레이션용)**

```
import boto3
import json
import os

class AwsTaskService(ITaskService):
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.queue_url = os.environ.get('SQS_QUEUE_URL')

    def submit_analysis_job(self, user_id: str, repo_url: str):
        print(f"[AWS] Submitting job for {repo_url} via SQS...")
        message_body = json.dumps({
            'user_id': user_id,
            'repo_url': repo_url
        })
        # Boto3 (AWS SDK)를 통해 SQS에 JSON 메시지 전송
        self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_body
        )

```

> 핵심: API 서버는 ITaskService에만 의존합니다. 로컬에서는 LocalTaskService를, AWS에서는 AwsTaskService를 주입(Dependency Injection)하기만 하면 코어 로직 수정 없이 환경을 전환할 수 있습니다.
> 

## 3. 🏠 1단계: 로컬 개발 계획 (Docker Compose)

- **목표:** 핵심 분석 로직 및 API 기능 100% 완성.
- **실행:** `docker-compose up --build`

**`docker-compose.yml` (설계안)**

```
version: '3.8'

services:
  # 1. API 서버 (FastAPI)
  web:
    build: ./api # API 서버의 Dockerfile 위치
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./api:/app # 실시간 코드 리로딩
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/github_analyzer
      - QUEUE_BROKER_URL=redis://queue:6379/0
      - TASK_SERVICE_IMPL=LOCAL # 'LocalTaskService'를 사용하도록 설정
    depends_on:
      - db
      - queue

  # 2. 분석 워커 (Celery)
  worker:
    build: ./worker # 워커의 Dockerfile 위치
    # Celery 워커 실행 명령어
    command: celery -A worker.celery_app worker --loglevel=info
    volumes:
      - ./worker:/app
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/github_analyzer
      - QUEUE_BROKER_URL=redis://queue:6379/0
    depends_on:
      - db
      - queue

  # 3. 데이터베이스 (PostgreSQL)
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=github_analyzer
    ports:
      - "5432:5432" # 로컬에서 DB 직접 접근용

  # 4. 작업 큐 (Redis)
  queue:
    image: redis:7
    ports:
      - "6379:6379" # 로컬에서 큐 직접 접근용

volumes:
  postgres_data: # DB 데이터 영속화

```

**로컬 개발 흐름**

1. **API (`web`):** `/analyze` 엔드포인트가 `LocalTaskService`를 호출.
2. **TaskService:** `analyze_repo_task.delay()`를 호출하여 `queue`(Redis)에 작업 적재.
3. **Worker (`worker`):** Celery가 `queue`를 감시하다 작업을 발견하고 실행.
4. **Worker 로직:**
    - GitHub 토큰으로 `git clone`.
    - `git blame` 실행 및 분석.
    - 분석 결과를 `db`(Postgres)에 저장.
5. **API (`web`):** `/results` 엔드포인트가 `db`를 조회하여 사용자에게 결과 반환.

## 4. ☁️ 2단계: AWS 마이그레이션 계획

- **목표:** 로컬에서 완성된 기능을 확장성, 안정성, 보안성이 확보된 AWS 환경으로 이식.

### 4.1. 아키텍처 다이어그램 (AWS)

### 4.2. 컴포넌트 마이그레이션 맵

| **로컬 (docker-compose)** | **➡️** | **AWS (프로덕션)** | **마이그레이션 공수 / "폼(Form)"** |
| --- | --- | --- | --- |
| **`web` (FastAPI)** | ➡️ | **Amazon ECS on Fargate** | **[하]** 로컬 이미지를 ECR에 푸시. Fargate 서비스 정의. |
| **`db` (Postgres)** | ➡️ | **Amazon RDS** | **[하]** RDS 인스턴스 생성. 스키마 마이그레이션. |
| **`queue` (Redis)** | ➡️ | **Amazon SQS** | **[중]** `LocalTaskService`를 `AwsTaskService`로 교체. (코드 수정) |
| **`worker` (Celery)** | ➡️ | **AWS Batch** | **[상]** 워커 로직 및 인프라 설정 변경. (아래 상세) |
| **`.env` (보안)** | ➡️ | **AWS Secrets Manager** | **[중]** DB 암호, GitHub 토큰 등을 저장하고, IAM Role로 접근. |

### 4.3. 핵심 마이그레이션: `Worker` (Celery → AWS Batch)

가장 큰 "폼(공수)"이 드는 부분입니다.

### A. 워커 코드(로직) 변경 (공수: 중)

Celery 의존성을 제거하고, AWS Batch가 실행할 단순 스크립트(`run_analysis.py`)를 만듭니다.

```
# worker/run_analysis.py (AWS Batch 실행 스크립트)
import os
import json
import boto3
from analysis.logic import run_full_analysis # 로컬에서 100% 재사용한 핵심 로직

def main():
    # 1. AWS Batch가 주입한 SQS 메시지(작업 내용)를 환경변수에서 읽기
    sqs_message_json = os.environ.get('SQS_MESSAGE_BODY')
    job_data = json.loads(sqs_message_json)
    user_id = job_data['user_id']
    repo_url = job_data['repo_url']

    # 2. (Secrets Manager에서 GitHub 토큰 가져오기)

    try:
        # 3. 핵심 분석 로직 실행 (로컬에서 100% 재활용)
        run_full_analysis(user_id, repo_url)

        # 4. 성공 시 SQS 메시지 삭제 (필수!)
        sqs_receipt_handle = os.environ.get('SQS_RECEIPT_HANDLE')
        sqs = boto3.client('sqs')
        sqs.delete_message(
            QueueUrl=os.environ.get('SQS_QUEUE_URL'),
            ReceiptHandle=sqs_receipt_handle
        )
        print("Job Succeeded.")

    except Exception as e:
        print(f"Job Failed: {e}")
        # 실패 시 메시지를 삭제하지 않으면, SQS가 Dead-Letter-Queue로 보내거나 재시도함
        raise e

if __name__ == "__main__":
    main()

```

- **Dockerfile (`worker/Dockerfile.aws`):**
    - `ENTRYPOINT ["python", "run_analysis.py"]` 로 변경 (Celery 명령어 대신)

### B. AWS 인프라 설정 (공수: 상)

이 "폼(Form)" 설정이 실제 작업의 대부분을 차지합니다.

1. **ECR (Elastic Container Registry):** `web`과 `worker`의 도커 이미지를 빌드하여 푸시합니다.
2. **IAM Roles (가장 중요):**
    - `Batch_Task_Role`: Batch 작업(컨테이너)이 SQS(메시지 읽기/삭제), RDS(DB 쓰기), Secrets Manager(토큰 읽기)에 접근할 권한.
    - `ECS_Task_Role`: `web`(API 서버)이 SQS(메시지 쓰기), RDS(DB 읽기), Secrets Manager(토큰 읽기)에 접근할 권한.
3. **SQS (Simple Queue Service):** 작업 대기열 생성 (표준 큐 또는 FIFO 큐).
4. **AWS Batch - Compute Environment:**
    - 워커가 실행될 EC2 인스턴스 사양(vCPU, Memory) 및 유형(On-Demand 또는 Spot) 정의.
    - VPC, Subnet, Security Group 설정.
5. **AWS Batch - Job Queue:**
    - 생성한 SQS 큐가 아닌, Batch 자체의 작업 큐를 생성하고 Compute Environment와 연결.
6. **AWS Batch - Job Definition:**
    - "어떤 ECR 이미지(`worker:latest`)를, 어떤 IAM Role(`Batch_Task_Role`)로, 어떤 vCPU/Memory를 할당하여 실행할 것인가"를 정의하는 **'명령서'**.
7. **"접착제" (Glue) - SQS와 Batch 연동:**
    - **Amazon EventBridge Pipe** 또는 **Lambda**를 사용하여 "SQS 큐에 메시지가 1개 이상 들어오면 -> AWS Batch Job을 Submit(실행)하라"는 트리거를 설정합니다. 이 파이프가 SQS 메시지 본문과 핸들(삭제용)을 Batch 작업의 환경 변수로 전달해줍니다.

이 계획을 따르면, 로컬에서 모든 핵심 로직을 빠르고 안전하게 개발한 뒤, AWS의 강력한 병렬 처리 및 관리형 서비스의 이점을 모두 누릴 수 있습니다.