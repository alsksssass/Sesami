# ====================================================================
# Nginx Dockerfile for Sesami
# ====================================================================
FROM nginx:1.25-alpine

# Nginx 설정 파일 복사
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Frontend 빌드 결과물을 복사할 디렉토리 생성
RUN mkdir -p /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Nginx 실행 (foreground)
CMD ["nginx", "-g", "daemon off;"]
