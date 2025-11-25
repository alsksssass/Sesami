# ====================================================================
# Frontend Dockerfile - Production Build
# ====================================================================
# Vite로 React 앱을 빌드하여 /app/dist에 정적 파일 생성
# Nginx가 이 디렉토리를 마운트하여 서빙
# ====================================================================

FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY src/frontend/package*.json ./
RUN npm ci

# 소스 코드 복사
COPY src/frontend/ ./

# 환경 변수 (빌드 시점에 API URL 설정)
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# 프로덕션 빌드
RUN npm run build

# 빌드 결과물 확인
RUN ls -la /app/dist

# CMD는 사용하지 않음 (Nginx가 dist 디렉토리 마운트)
CMD ["echo", "Frontend build complete. Nginx will serve /app/dist"]
