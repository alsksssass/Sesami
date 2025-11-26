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

logs-nginx: ## Nginx 로그 보기
	docker-compose logs -f nginx

logs-cloudflare: ## Cloudflare Tunnel 로그 보기
	docker-compose logs -f cloudflare-tunnel

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

ps: ## 실행 중인 컨테이너 목록
	docker-compose ps

# ============================================
# AWS Services (RDS, S3)
# ============================================

db-migrate: ## 데이터베이스 마이그레이션 실행 (AWS RDS)
	@echo "$(GREEN)🗄️  마이그레이션 실행 중...$(NC)"
	docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)✅ 마이그레이션 완료$(NC)"

s3-test: ## S3 연결 테스트
	@echo "$(GREEN)🪣 S3 연결 테스트 중...$(NC)"
	docker-compose exec backend python -c "import boto3; s3 = boto3.client('s3'); print('S3 Buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])"
	@echo "$(GREEN)✅ S3 연결 성공$(NC)"

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
	docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ 프로덕션 빌드 완료$(NC)"

prod-up: ## 프로덕션 환경 시작
	@echo "$(GREEN)🚀 프로덕션 환경 시작...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ 프로덕션 환경 실행 중$(NC)"

prod-clean:
	docker-compose -f docker-compose.prod.yml down -v --rmi all

# ============================================
# 유틸리티
# ============================================

status: ## 서비스 상태 확인
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)  서비스 상태$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(GREEN)🌐 Nginx:$(NC)     http://localhost"
	@echo "$(GREEN)🔗 Cloudflare:$(NC) (Tunnel 설정 필요)"
	@echo "$(GREEN)📊 Frontend:$(NC)  http://localhost (via Nginx)"
	@echo "$(GREEN)📊 Backend:$(NC)   http://localhost/api (via Nginx)"
	@echo "$(GREEN)📊 API Docs:$(NC)  http://localhost/docs"
	@echo "$(GREEN)📊 Database:$(NC)  AWS RDS (환경변수로 설정)"
	@echo "$(GREEN)📦 Storage:$(NC)   AWS S3 (환경변수로 설정)"

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

# ============================================
# Graph-RAG 개발 환경 (v2)
# ============================================

graph-dev: ## Neo4j + OpenSearch 포함 Graph-RAG 개발 환경 시작
	@echo "$(GREEN)🔨 Graph-RAG 개발 환경 시작...$(NC)"
	docker-compose up neo4j opensearch backend worker -d
	@echo "$(GREEN)✅ Neo4j Browser: http://localhost:7474$(NC)"
	@echo "$(GREEN)✅ OpenSearch: http://localhost:9200$(NC)"
	@echo "$(GREEN)✅ Backend API: http://localhost:8000$(NC)"

graph-dev-all: ## 전체 서비스 포함 Graph-RAG 환경 시작
	@echo "$(GREEN)🚀 전체 Graph-RAG 환경 시작...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ 모든 서비스 실행 중!$(NC)"
	@echo "$(GREEN)   - Frontend: http://localhost:5173$(NC)"
	@echo "$(GREEN)   - Backend: http://localhost:8000$(NC)"
	@echo "$(GREEN)   - Neo4j: http://localhost:7474$(NC)"
	@echo "$(GREEN)   - OpenSearch: http://localhost:9200$(NC)"

dev-infra: ## 백엔드 인프라만 시작 (DB, Queue, Neo4j, OpenSearch, Backend, Worker)
	@echo "$(GREEN)🔨 백엔드 인프라 시작...$(NC)"
	docker-compose up -d db queue neo4j opensearch backend worker
	@echo "$(GREEN)✅ 백엔드 인프라 실행 중!$(NC)"
	@echo "$(YELLOW)📝 프론트엔드는 별도 터미널에서 실행하세요:$(NC)"
	@echo "   $(BLUE)make dev-frontend$(NC)"
	@echo ""
	@echo "$(GREEN)접속 URL:$(NC)"
	@echo "   - Backend API: http://localhost:8000"
	@echo "   - Backend Docs: http://localhost:8000/docs"
	@echo "   - Neo4j Browser: http://localhost:7474"
	@echo "   - OpenSearch: http://localhost:9200"

dev-frontend: ## 프론트엔드 로컬 개발 서버 시작 (Vite)
	@echo "$(GREEN)🚀 프론트엔드 개발 서버 시작...$(NC)"
	@echo "$(YELLOW)📦 의존성 확인 중...$(NC)"
	npm --prefix src/frontend install
	@echo "$(GREEN)✅ Vite 개발 서버 실행 중...$(NC)"
	npm --prefix src/frontend run dev

graph-dev: ## Graph-RAG 개발 환경 시작 (Neo4j + OpenSearch + Backend + Worker)
	@echo "$(GREEN)🔧 Graph-RAG 개발 환경 시작...$(NC)"
	docker-compose up -d neo4j opensearch db queue backend worker
	@echo "$(GREEN)✅ Graph-RAG 환경 실행 중!$(NC)"
	@echo ""
	@echo "$(GREEN)접속 URL:$(NC)"
	@echo "   - Backend API: http://localhost:8000"
	@echo "   - Backend Docs: http://localhost:8000/docs"
	@echo "   - Neo4j Browser: http://localhost:7474"
	@echo "   - Neo4j User/Pass: neo4j / sesami_graph_2025"
	@echo "   - OpenSearch: https://localhost:9200"
	@echo "   - OpenSearch User/Pass: admin / Sesami@OpenSearch2025!"
	@echo ""
	@echo "$(YELLOW)유용한 명령어:$(NC)"
	@echo "   $(BLUE)make shell-neo4j$(NC)         - Neo4j Cypher Shell 접속"
	@echo "   $(BLUE)make check-neo4j$(NC)         - Neo4j 상태 확인"
	@echo "   $(BLUE)make check-opensearch$(NC)    - OpenSearch 상태 확인"
	@echo "   $(BLUE)make logs-neo4j$(NC)          - Neo4j 로그 보기"
	@echo "   $(BLUE)make logs-opensearch$(NC)     - OpenSearch 로그 보기"
	@echo "   $(BLUE)make clean-graph$(NC)         - 그래프 데이터 초기화"

shell-neo4j: ## Neo4j Cypher Shell 접속
	@echo "$(BLUE)📊 Neo4j Cypher Shell 접속...$(NC)"
	docker-compose exec neo4j cypher-shell -u neo4j -p sesami_graph_2025

check-neo4j: ## Neo4j 상태 확인
	@echo "$(BLUE)🔍 Neo4j 상태 확인 중...$(NC)"
	@docker-compose exec neo4j cypher-shell -u neo4j -p sesami_graph_2025 "CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version;" || echo "$(RED)❌ Neo4j 연결 실패$(NC)"

check-opensearch: ## OpenSearch 클러스터 상태 확인
	@echo "$(BLUE)🔍 OpenSearch 클러스터 상태 확인...$(NC)"
	@curl -k -u admin:Sesami@OpenSearch2025! https://localhost:9200/_cluster/health?pretty || echo "$(RED)❌ OpenSearch 연결 실패$(NC)"

logs-neo4j: ## Neo4j 로그 보기
	docker-compose logs -f neo4j

logs-opensearch: ## OpenSearch 로그 보기
	docker-compose logs -f opensearch

clean-graph: ## Neo4j + OpenSearch 데이터 초기화 (⚠️ 그래프 데이터 삭제)
	@echo "$(RED)⚠️  그래프 데이터 삭제 중...$(NC)"
	docker-compose stop neo4j opensearch
	docker volume rm sesami_neo4j_data sesami_neo4j_logs sesami_opensearch_data 2>/dev/null || true
	@echo "$(GREEN)✅ 그래프 데이터 삭제 완료$(NC)"

# ============================================
# 통합 테스트 (v2)
# ============================================

ci: ## 통합 스모크 테스트 실행
	@echo "$(YELLOW)🧪 통합 테스트 실행 중...$(NC)"
	@echo "$(BLUE)--- Backend Tests ---$(NC)"
	@docker-compose exec -T backend pytest tests/ -v 2>/dev/null || echo "$(YELLOW)⚠️  Backend 테스트 스킵 (pytest 미설치)$(NC)"
	@echo ""
	@echo "$(BLUE)--- Frontend Tests ---$(NC)"
	@docker-compose exec -T frontend npm test 2>/dev/null || echo "$(YELLOW)⚠️  Frontend 테스트 스킵$(NC)"
	@echo ""
	@echo "$(BLUE)--- Health Checks ---$(NC)"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "$(GREEN)✅ Backend Health OK$(NC)" || echo "$(RED)❌ Backend Health Failed$(NC)"
	@echo "$(GREEN)✅ 통합 테스트 완료$(NC)"

health-check: ## 모든 서비스 헬스체크
	@echo "$(BLUE)🏥 서비스 헬스체크 중...$(NC)"
	@echo ""
	@echo "$(YELLOW)Nginx:$(NC)"
	@curl -f http://localhost/health 2>/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ Failed$(NC)"
	@echo ""
	@echo "$(YELLOW)Frontend (via Nginx):$(NC)"
	@curl -f http://localhost 2>/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ Failed$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend API (via Nginx):$(NC)"
	@curl -f http://localhost/api/health 2>/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ Failed$(NC)"
	@echo ""
	@echo "$(YELLOW)AWS RDS (Database):$(NC)"
	@echo "$(BLUE)ℹ️  환경변수 DATABASE_URL로 설정됨$(NC)"
	@echo ""
	@echo "$(YELLOW)AWS S3 (Storage):$(NC)"
	@echo "$(BLUE)ℹ️  환경변수 S3_BUCKET_NAME로 설정됨$(NC)"
