FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache curl

# package.json과 package-lock.json 복사
COPY src/frontend/package*.json ./

# 의존성 설치
RUN npm install

# 소스 코드는 볼륨 마운트로 처리

EXPOSE 5173

CMD ["npm", "run", "dev"]
