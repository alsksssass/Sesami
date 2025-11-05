.PHONY: help build rebuild up down restart logs clean dev prod install test

# 기본 타겟
.DEFAULT_GOAL := help

# 색상 정의
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## 사용 가능한 명령어 목록 표시
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  Sesami - GitHub Analyzer$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# 개발 환경
# ============================================

dev: ## 개발 환경 시작 (핫 리로딩)
	@echo "$(GREEN)🚀 개발 환경 시작...$(NC)"
	docker-compose up

dev-d: ## 개발 환경 백그라운드 시작
	@echo "$(GREEN)🚀 개발 환경 백그라운드 시작...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ 실행 중! 로그 보기: make logs$(NC)"

stop: ## 모든 컨테이너 중지
	@echo "$(YELLOW)⏸️  컨테이너 중지 중...$(NC)"
	docker-compose stop
	@echo "$(GREEN)✅ 중지 완료$(NC)"

down: ## 모든 컨테이너 중지 및 삭제
	@echo "$(YELLOW)🗑️  컨테이너 중지 및 삭제 중...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ 삭제 완료$(NC)"

restart: ## 모든 서비스 재시작
	@echo "$(YELLOW)🔄 서비스 재시작 중...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✅ 재시작 완료$(NC)"

# ============================================
# 빌드
# ============================================

build: ## 모든 이미지 빌드
	@echo "$(GREEN)🔨 이미지 빌드 중...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ 빌드 완료$(NC)"

rebuild: ## 캐시 없이 모든 이미지 재빌드
	@echo "$(RED)🔨 캐시 제거 후 재빌드 중...$(NC)"
	docker-compose build --no-cache --pull
	@echo "$(GREEN)✅ 재빌드 완료$(NC)"

build-frontend: ## 프론트엔드만 빌드
	@echo "$(GREEN)🔨 프론트엔드 빌드 중...$(NC)"
	docker-compose build frontend
	@echo "$(GREEN)✅ 프론트엔드 빌드 완료$(NC)"

build-backend: ## 백엔드만 빌드
	@echo "$(GREEN)🔨 백엔드 빌드 중...$(NC)"
	docker-compose build backend
	@echo "$(GREEN)✅ 백엔드 빌드 완료$(NC)"

build-worker: ## 워커만 빌드
	@echo "$(GREEN)🔨 워커 빌드 중...$(NC)"
	docker-compose build worker
	@echo "$(GREEN)✅ 워커 빌드 완료$(NC)"

rebuild-frontend: ## 프론트엔드만 재빌드 (캐시 무효화)
	@echo "$(RED)🔨 프론트엔드 재빌드 중...$(NC)"
	docker-compose build --no-cache --pull frontend
	@echo "$(GREEN)✅ 프론트엔드 재빌드 완료$(NC)"

rebuild-backend: ## 백엔드만 재빌드 (캐시 무효화)
	@echo "$(RED)🔨 백엔드 재빌드 중...$(NC)"
	docker-compose build --no-cache --pull backend
	@echo "$(GREEN)✅ 백엔드 재빌드 완료$(NC)"

rebuild-worker: ## 워커만 재빌드 (캐시 무효화)
	@echo "$(RED)🔨 워커 재빌드 중...$(NC)"
	docker-compose build --no-cache --pull worker
	@echo "$(GREEN)✅ 워커 재빌드 완료$(NC)"

# ============================================
# 실행 (빌드 + 시작)
# ============================================

up: build ## 빌드 후 개발 환경 시작
	@echo "$(GREEN)🚀 빌드 후 시작...$(NC)"
	docker-compose up

up-d: build ## 빌드 후 백그라운드 시작
	@echo "$(GREEN)🚀 빌드 후 백그라운드 시작...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ 실행 중! 로그 보기: make logs$(NC)"

fresh: rebuild ## 재빌드 후 개발 환경 시작 (완전 초기화)
	@echo "$(GREEN)🚀 재빌드 후 시작...$(NC)"
	docker-compose up

fresh-d: rebuild ## 재빌드 후 백그라운드 시작
	@echo "$(GREEN)🚀 재빌드 후 백그라운드 시작...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ 실행 중! 로그 보기: make logs$(NC)"

# ============================================
# 로그
# ============================================

logs: ## 모든 서비스 로그 보기
	docker-compose logs -f

logs-frontend: ## 프론트엔드 로그만 보기
	docker-compose logs -f frontend

logs-backend: ## 백엔드 로그만 보기
	docker-compose logs -f backend

logs-worker: ## 워커 로그만 보기
	docker-compose logs -f worker

logs-db: ## 데이터베이스 로그 보기
	docker-compose logs -f db

logs-queue: ## Redis 큐 로그 보기
	docker-compose logs -f queue

# ============================================
# 클린업
# ============================================

clean: ## 컨테이너, 볼륨, 이미지 모두 삭제
	@echo "$(RED)🗑️  모든 리소스 삭제 중...$(NC)"
	docker-compose down -v --rmi all
	@echo "$(GREEN)✅ 삭제 완료$(NC)"

clean-volumes: ## 볼륨만 삭제 (DB 데이터 초기화)
	@echo "$(RED)🗑️  볼륨 삭제 중... (DB 데이터 초기화)$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✅ 볼륨 삭제 완료$(NC)"

clean-images: ## 이미지만 삭제
	@echo "$(RED)🗑️  이미지 삭제 중...$(NC)"
	docker-compose down --rmi all
	@echo "$(GREEN)✅ 이미지 삭제 완료$(NC)"

prune: ## Docker 시스템 정리 (사용하지 않는 리소스 삭제)
	@echo "$(RED)🗑️  Docker 시스템 정리 중...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✅ 정리 완료$(NC)"

# ============================================
# 개발 도구
# ============================================

shell-frontend: ## 프론트엔드 컨테이너 쉘 접속
	docker-compose exec frontend sh

shell-backend: ## 백엔드 컨테이너 쉘 접속
	docker-compose exec backend sh

shell-worker: ## 워커 컨테이너 쉘 접속
	docker-compose exec worker sh

shell-db: ## 데이터베이스 컨테이너 쉘 접속
	docker-compose exec db psql -U github_user -d github_db

ps: ## 실행 중인 컨테이너 목록
	docker-compose ps

# ============================================
# 데이터베이스
# ============================================

db-migrate: ## 데이터베이스 마이그레이션 실행
	@echo "$(GREEN)🗄️  마이그레이션 실행 중...$(NC)"
	docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)✅ 마이그레이션 완료$(NC)"

db-reset: ## 데이터베이스 초기화 (위험!)
	@echo "$(RED)⚠️  데이터베이스 초기화 중...$(NC)"
	docker-compose down -v
	docker-compose up -d db
	@sleep 3
	docker-compose up -d backend
	@echo "$(GREEN)✅ 데이터베이스 초기화 완료$(NC)"

# ============================================
# 테스트
# ============================================

test: ## 테스트 실행
	@echo "$(GREEN)🧪 테스트 실행 중...$(NC)"
	docker-compose exec backend pytest
	@echo "$(GREEN)✅ 테스트 완료$(NC)"

test-frontend: ## 프론트엔드 테스트 실행
	@echo "$(GREEN)🧪 프론트엔드 테스트 실행 중...$(NC)"
	docker-compose exec frontend npm test
	@echo "$(GREEN)✅ 테스트 완료$(NC)"

# ============================================
# 프로덕션
# ============================================

prod-build: ## 프로덕션 빌드
	@echo "$(GREEN)🔨 프로덕션 빌드 중...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ 프로덕션 빌드 완료$(NC)"

prod-up: ## 프로덕션 환경 시작
	@echo "$(GREEN)🚀 프로덕션 환경 시작...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ 프로덕션 환경 실행 중$(NC)"

# ============================================
# 유틸리티
# ============================================

status: ## 서비스 상태 확인
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  서비스 상태$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(GREEN)📊 Frontend:$(NC) http://localhost:3000"
	@echo "$(GREEN)📊 Backend:$(NC)  http://localhost:8000"
	@echo "$(GREEN)📊 API Docs:$(NC) http://localhost:8000/docs"
	@echo "$(GREEN)📊 Database:$(NC) localhost:5432"
	@echo "$(GREEN)📊 Redis:$(NC)    localhost:6379"

install: ## 로컬 개발 환경 설정 (node_modules, venv 등)
	@echo "$(GREEN)📦 의존성 설치 중...$(NC)"
	@echo "프론트엔드 의존성..."
	cd src/frontend && npm install
	@echo "백엔드 의존성..."
	cd src/backend && pip install -r requirements.txt
	@echo "$(GREEN)✅ 설치 완료$(NC)"

check-env: ## .env 파일 확인
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  환경 변수 확인$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✅ .env 파일 존재$(NC)"; \
		echo ""; \
		cat .env; \
	else \
		echo "$(RED)❌ .env 파일 없음!$(NC)"; \
		echo "$(YELLOW)⚠️  .env.example 파일을 .env로 복사하세요.$(NC)"; \
	fi

version: ## 버전 정보 표시
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  Sesami - GitHub Analyzer$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
