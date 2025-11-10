FROM python:3.11-alpine

WORKDIR /app

# 시스템 패키지 설치 (Alpine은 apk 사용)
RUN apk add --no-cache \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

# requirements.txt 복사 및 의존성 설치
COPY ../../src/backend/requirements.txt .
COPY ../../src/shared /shared
ENV PYTHONPATH=/app:/shared
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드는 볼륨 마운트로 처리

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
