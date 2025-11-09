# AWS 마이그레이션 전략

## 🎯 마이그레이션 목표

로컬 Docker Compose 환경에서 검증된 시스템을 AWS 프로덕션 환경으로 전환:
- ✅ 무중단 확장성 (Auto Scaling)
- ✅ 관리형 서비스 활용 (RDS, SQS, Batch)
- ✅ 보안 강화 (Secrets Manager, IAM)
- ✅ 비용 최적화 (Spot Instances, Reserved Capacity)

---

## 📊 컴포넌트 마이그레이션 매핑

| 로컬 (Docker Compose) | AWS 서비스 | 공수 | 마이그레이션 방식 |
|----------------------|-----------|------|------------------|
| `frontend` (React) | **CloudFront + S3** | 하 | Static build → S3 bucket |
| `backend` (FastAPI) | **ECS on Fargate** | 중 | Docker image → ECR → ECS |
| `db` (PostgreSQL) | **Amazon RDS** | 하 | `pg_dump` → RDS restore |
| `queue` (Redis) | **Amazon SQS** | 중 | TaskService 교체 |
| `worker` (Celery) | **AWS Batch** | 상 | Worker 로직 + 인프라 재설계 |
| `.env` | **Secrets Manager** | 중 | 환경변수 → Secrets 이관 |
| - | **ECR** | 하 | Docker 이미지 저장소 |
| - | **VPC + Security Groups** | 중 | 네트워크 격리 |

---

## 🏗️ AWS 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Public Internet                                       │     │
│  │  ┌────────────┐          ┌────────────┐               │     │
│  │  │ CloudFront │          │   Route53  │               │     │
│  │  │  + S3      │          │    DNS     │               │     │
│  │  └──────┬─────┘          └──────┬─────┘               │     │
│  │         │ Static Assets         │                      │     │
│  └─────────┼───────────────────────┼──────────────────────┘     │
│            │                       │                            │
│  ┌─────────▼───────────────────────▼──────────────────────┐     │
│  │  Application Load Balancer (ALB)                       │     │
│  │  - HTTPS (ACM Certificate)                             │     │
│  │  - Health Checks                                       │     │
│  └─────────┬──────────────────────────────────────────────┘     │
│            │                                                    │
│  ┌─────────▼──────────────────────────────────────────────┐     │
│  │  VPC (Private Subnets)                                 │     │
│  │                                                         │     │
│  │  ┌──────────────────────────────────────────────┐      │     │
│  │  │  ECS Cluster (Fargate)                       │      │     │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐                │      │     │
│  │  │  │ API  │  │ API  │  │ API  │                │      │     │
│  │  │  │ Task │  │ Task │  │ Task │                │      │     │
│  │  │  └───┬──┘  └───┬──┘  └───┬──┘                │      │     │
│  │  │      └──────────┴─────────┘                   │      │     │
│  │  │         (Auto Scaling: 2-10 tasks)            │      │     │
│  │  └──────────────────┬───────────────────────────┘      │     │
│  │                     │                                   │     │
│  │                     │ Submit Jobs                       │     │
│  │                     ▼                                   │     │
│  │  ┌──────────────────────────────────────────────┐      │     │
│  │  │  Amazon SQS (Job Queue)                      │      │     │
│  │  │  - Standard Queue                            │      │     │
│  │  │  - DLQ (Dead Letter Queue)                   │      │     │
│  │  └──────────────────┬───────────────────────────┘      │     │
│  │                     │                                   │     │
│  │                     │ Trigger (EventBridge/Lambda)      │     │
│  │                     ▼                                   │     │
│  │  ┌──────────────────────────────────────────────┐      │     │
│  │  │  AWS Batch                                   │      │     │
│  │  │  ┌─────────────────────────────────────┐     │      │     │
│  │  │  │ Compute Environment                 │     │      │     │
│  │  │  │ - EC2 (Spot Instances)              │     │      │     │
│  │  │  │ - Auto Scaling (0-100)              │     │      │     │
│  │  │  └─────────────────────────────────────┘     │      │     │
│  │  │  ┌─────────────────────────────────────┐     │      │     │
│  │  │  │ Job Definition (Worker Container)   │     │      │     │
│  │  │  │ - ECR Image: worker:latest          │     │      │     │
│  │  │  │ - IAM Role: BatchTaskRole           │     │      │     │
│  │  │  │ - vCPU: 4, Memory: 8 GB             │     │      │     │
│  │  │  └─────────────────────────────────────┘     │      │     │
│  │  └──────────────────────────────────────────────┘      │     │
│  │                                                         │     │
│  │  ┌──────────────────────────────────────────────┐      │     │
│  │  │  Amazon RDS (PostgreSQL)                     │      │     │
│  │  │  - Multi-AZ                                  │      │     │
│  │  │  - Automated Backups                         │      │     │
│  │  │  - Read Replicas (선택적)                    │      │     │
│  │  └──────────────────────────────────────────────┘      │     │
│  │                                                         │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AWS Secrets Manager                                    │    │
│  │  - GitHub OAuth Credentials                             │    │
│  │  - DB Password                                          │    │
│  │  - JWT Secret                                           │    │
│  │  - Encryption Keys                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CloudWatch                                             │    │
│  │  - Logs (API, Worker, RDS)                              │    │
│  │  - Metrics (Latency, Error Rate)                        │    │
│  │  - Alarms (SNS Notifications)                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 핵심 마이그레이션: Worker (Celery → AWS Batch)

### 1. AWS Batch 개념

**AWS Batch**:
- Docker 컨테이너로 배치 작업 실행
- EC2 인스턴스 자동 관리 (Spot/On-Demand)
- 큐 깊이 기반 Auto Scaling
- SQS 메시지를 Job Parameter로 전달

**구성 요소**:
1. **Compute Environment**: Worker가 실행될 EC2 인스턴스 풀
2. **Job Queue**: Batch Job 대기열 (≠ SQS)
3. **Job Definition**: Docker 이미지, 리소스 할당, IAM Role
4. **Job Submission**: SQS → EventBridge/Lambda → Batch Job

### 2. Worker 코드 변경

#### 기존 (Celery)
```python
# src/worker/tasks.py
from celery_app import app

@app.task
def analyze_repository(user_id, repo_url):
    # 분석 로직
    pass
```

#### 변경 후 (AWS Batch)
```python
# src/worker/run_analysis.py
import os
import json
import boto3
from analysis.git_analyzer import GitAnalyzer
from database import SessionLocal
from models import AnalysisJob

def main():
    # 1. 환경변수에서 SQS 메시지 읽기
    sqs_message_body = os.environ['SQS_MESSAGE_BODY']
    job_data = json.loads(sqs_message_body)

    user_id = job_data['user_id']
    repo_url = job_data['repo_url']
    job_id = job_data['job_id']

    # 2. Secrets Manager에서 GitHub 토큰 가져오기
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(
        SecretId=f'github-token-{user_id}'
    )
    access_token = json.loads(secret['SecretString'])['access_token']

    # 3. 데이터베이스 업데이트 (PROCESSING)
    db = SessionLocal()
    job = db.query(AnalysisJob).filter_by(id=job_id).first()
    job.status = 'PROCESSING'
    db.commit()

    try:
        # 4. Git 분석 실행 (로컬과 동일한 로직)
        analyzer = GitAnalyzer(repo_url, access_token)
        analyzer.clone_repository()

        blame_result = analyzer.analyze_blame(user_id)
        tech_stack = analyzer.analyze_tech_stack()

        analyzer.cleanup()

        # 5. 결과 저장 (COMPLETED)
        job.status = 'COMPLETED'
        job.result = {
            'contribution': blame_result,
            'tech_stack': tech_stack
        }
        db.commit()

        # 6. SQS 메시지 삭제 (성공 시)
        sqs = boto3.client('sqs')
        sqs.delete_message(
            QueueUrl=os.environ['SQS_QUEUE_URL'],
            ReceiptHandle=os.environ['SQS_RECEIPT_HANDLE']
        )

        print(f"Job {job_id} completed successfully")

    except Exception as e:
        # 실패 시 FAILED로 업데이트
        job.status = 'FAILED'
        job.error_message = str(e)
        db.commit()
        print(f"Job {job_id} failed: {e}")
        raise  # 재시도를 위해 예외 발생

    finally:
        db.close()

if __name__ == '__main__':
    main()
```

#### Dockerfile 변경
```dockerfile
# docker/worker/Dockerfile.aws
FROM python:3.12-slim

WORKDIR /app

# Git + AWS CLI
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY src/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt boto3

# 소스 코드
COPY src/worker/ ./

# AWS Batch Entry Point
ENTRYPOINT ["python", "run_analysis.py"]
```

### 3. Backend TaskService 변경

```python
# src/backend/common/task_service/aws_service.py
import boto3
import json
from .base import ITaskService

class AwsTaskService(ITaskService):
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.queue_url = os.environ['SQS_QUEUE_URL']

    def submit_analysis_job(self, user_id: str, repo_url: str, job_id: str):
        """SQS에 작업 메시지 전송"""
        message_body = json.dumps({
            'user_id': user_id,
            'repo_url': repo_url,
            'job_id': job_id
        })

        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_body
        )

        print(f"[AWS] Submitted job {job_id} to SQS: {response['MessageId']}")
        return response['MessageId']
```

```python
# src/backend/common/task_dependencies.py
import os
from .task_service.local_service import LocalTaskService
from .task_service.aws_service import AwsTaskService

def get_task_service():
    """환경에 따라 적절한 TaskService 반환"""
    impl = os.environ.get('TASK_SERVICE_IMPL', 'LOCAL')

    if impl == 'AWS':
        return AwsTaskService()
    else:
        return LocalTaskService()
```

---

## 🛠️ AWS 인프라 구축 단계

### Phase 1: 기본 인프라 (IaC with Terraform/CDK)

#### 1. VPC 및 네트워크
```hcl
# terraform/vpc.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = {
    Name = "sesami-vpc"
  }
}

resource "aws_subnet" "private" {
  count = 2
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "sesami-private-${count.index + 1}"
  }
}

resource "aws_subnet" "public" {
  count = 2
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.${count.index + 101}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "sesami-public-${count.index + 1}"
  }
}
```

#### 2. RDS (PostgreSQL)
```hcl
# terraform/rds.tf
resource "aws_db_instance" "main" {
  identifier = "sesami-db"
  engine = "postgres"
  engine_version = "15.4"
  instance_class = "db.t4g.micro"  # 개발: micro, 프로덕션: db.r6g.large

  allocated_storage = 20
  storage_type = "gp3"
  storage_encrypted = true

  db_name = "sesami_db"
  username = "sesami_admin"
  password = random_password.db_password.result  # Secrets Manager 연동

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name = aws_db_subnet_group.main.name

  multi_az = true  # 고가용성
  backup_retention_period = 7
  backup_window = "03:00-04:00"
  maintenance_window = "mon:04:00-mon:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "sesami-db-final-snapshot"

  tags = {
    Name = "sesami-rds"
  }
}
```

#### 3. ECR (Container Registry)
```hcl
# terraform/ecr.tf
resource "aws_ecr_repository" "backend" {
  name = "sesami/backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "worker" {
  name = "sesami/worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
```

### Phase 2: ECS (Backend API)

```hcl
# terraform/ecs.tf
resource "aws_ecs_cluster" "main" {
  name = "sesami-cluster"

  setting {
    name = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family = "sesami-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode = "awsvpc"
  cpu = "512"
  memory = "1024"
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8000
      protocol = "tcp"
    }]

    environment = [
      { name = "TASK_SERVICE_IMPL", value = "AWS" },
      { name = "SQS_QUEUE_URL", value = aws_sqs_queue.jobs.url }
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.db_url.arn}" },
      { name = "JWT_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.jwt_secret.arn}" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group" = "/ecs/sesami-backend"
        "awslogs-region" = "ap-northeast-2"
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name = "sesami-backend"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count = 2
  launch_type = "FARGATE"

  network_configuration {
    subnets = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name = "backend"
    container_port = 8000
  }

  # Auto Scaling
  depends_on = [aws_lb_listener.https]
}

resource "aws_appautoscaling_target" "ecs_service" {
  max_capacity = 10
  min_capacity = 2
  resource_id = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name = "ecs-cpu-autoscaling"
  policy_type = "TargetTrackingScaling"
  resource_id = aws_appautoscaling_target.ecs_service.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_service.scalable_dimension
  service_namespace = aws_appautoscaling_target.ecs_service.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

### Phase 3: AWS Batch (Worker)

```hcl
# terraform/batch.tf
resource "aws_batch_compute_environment" "main" {
  compute_environment_name = "sesami-worker-env"
  type = "MANAGED"
  service_role = aws_iam_role.batch_service.arn

  compute_resources {
    type = "SPOT"  # 비용 절감
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"
    bid_percentage = 100

    instance_types = ["c5.xlarge", "c5.2xlarge", "c6i.xlarge"]
    min_vcpus = 0
    max_vcpus = 256
    desired_vcpus = 0

    subnets = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.batch.id]
    instance_role = aws_iam_instance_profile.batch_instance.arn
  }
}

resource "aws_batch_job_queue" "main" {
  name = "sesami-job-queue"
  state = "ENABLED"
  priority = 1

  compute_environments = [aws_batch_compute_environment.main.arn]
}

resource "aws_batch_job_definition" "worker" {
  name = "sesami-worker"
  type = "container"
  platform_capabilities = ["EC2"]

  container_properties = jsonencode({
    image = "${aws_ecr_repository.worker.repository_url}:latest"
    vcpus = 4
    memory = 8192
    jobRoleArn = aws_iam_role.batch_task.arn

    environment = [
      { name = "SQS_QUEUE_URL", value = aws_sqs_queue.jobs.url }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group" = "/aws/batch/sesami-worker"
        "awslogs-region" = "ap-northeast-2"
      }
    }
  })
}
```

### Phase 4: SQS + EventBridge 연동

```hcl
# terraform/sqs.tf
resource "aws_sqs_queue" "jobs" {
  name = "sesami-analysis-jobs"
  visibility_timeout_seconds = 900  # 15분
  message_retention_seconds = 1209600  # 14일

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount = 3
  })
}

resource "aws_sqs_queue" "dlq" {
  name = "sesami-analysis-jobs-dlq"
  message_retention_seconds = 1209600
}

# EventBridge Pipe: SQS → Batch
resource "aws_pipes_pipe" "sqs_to_batch" {
  name = "sesami-sqs-to-batch"
  role_arn = aws_iam_role.eventbridge_pipe.arn

  source = aws_sqs_queue.jobs.arn
  source_parameters {
    sqs_queue_parameters {
      batch_size = 1
    }
  }

  target = aws_batch_job_queue.main.arn
  target_parameters {
    batch_job_parameters {
      job_definition = aws_batch_job_definition.worker.arn
      job_name = "analysis-job-$.messageId"

      container_overrides {
        environment = [
          {
            name = "SQS_MESSAGE_BODY"
            value = "$.body"
          },
          {
            name = "SQS_RECEIPT_HANDLE"
            value = "$.receiptHandle"
          }
        ]
      }
    }
  }
}
```

---

## 🔐 IAM Roles 설계

```hcl
# terraform/iam.tf

# ECS Task Execution Role (ECR pull, CloudWatch logs)
resource "aws_iam_role" "ecs_execution" {
  name = "sesami-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (SQS, Secrets Manager)
resource "aws_iam_role" "ecs_task" {
  name = "sesami-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task" {
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["sqs:SendMessage"]
        Resource = [aws_sqs_queue.jobs.arn]
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:*:*:secret:sesami/*"]
      }
    ]
  })
}

# Batch Task Role (SQS, RDS, Secrets Manager)
resource "aws_iam_role" "batch_task" {
  name = "sesami-batch-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "batch_task" {
  role = aws_iam_role.batch_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage"]
        Resource = [aws_sqs_queue.jobs.arn]
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:*:*:secret:sesami/*"]
      },
      {
        Effect = "Allow"
        Action = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = ["arn:aws:logs:*:*:log-group:/aws/batch/*"]
      }
    ]
  })
}
```

---

## 📦 배포 프로세스

### 1. Docker 이미지 빌드 및 푸시
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# Backend 이미지
docker build -f docker/backend/Dockerfile -t sesami/backend:latest .
docker tag sesami/backend:latest <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/sesami/backend:latest
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/sesami/backend:latest

# Worker 이미지
docker build -f docker/worker/Dockerfile.aws -t sesami/worker:latest .
docker tag sesami/worker:latest <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/sesami/worker:latest
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/sesami/worker:latest
```

### 2. 데이터베이스 마이그레이션
```bash
# 로컬 DB 백업
docker-compose exec db pg_dump -U sesami_user sesami_db > backup.sql

# RDS로 복원
psql -h <rds-endpoint> -U sesami_admin -d sesami_db -f backup.sql
```

### 3. Secrets Manager 설정
```bash
# GitHub OAuth
aws secretsmanager create-secret \
  --name sesami/github-oauth \
  --secret-string '{"client_id":"xxx","client_secret":"yyy"}'

# JWT Secret
aws secretsmanager create-secret \
  --name sesami/jwt-secret \
  --secret-string '{"key":"your-jwt-secret-key"}'

# DB URL
aws secretsmanager create-secret \
  --name sesami/database-url \
  --secret-string "postgresql://sesami_admin:password@<rds-endpoint>:5432/sesami_db"
```

### 4. Terraform 배포
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. ECS 서비스 배포
```bash
# Task Definition 업데이트
aws ecs register-task-definition --cli-input-json file://backend-task-def.json

# 서비스 업데이트 (Rolling Update)
aws ecs update-service \
  --cluster sesami-cluster \
  --service sesami-backend \
  --task-definition sesami-backend:latest \
  --desired-count 2
```

---

## 💰 비용 최적화 전략

1. **Spot Instances (Batch)**: 70% 비용 절감
2. **Fargate Savings Plan**: 30-50% 할인
3. **RDS Reserved Instances**: 1년 예약 40% 할인
4. **Auto Scaling**: 유휴 리소스 최소화
5. **CloudWatch Logs 보존 기간**: 7일 (개발), 30일 (프로덕션)

---

**다음 문서**: [06_IMPLEMENTATION_PLAN.md](./06_IMPLEMENTATION_PLAN.md) - 구현 우선순위 및 일정
