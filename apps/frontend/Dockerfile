# --- 1. Build Stage ---
FROM node:18-alpine as builder

WORKDIR /app

# package.json과 package-lock.json을 먼저 복사하여 종속성 캐싱 활용
COPY package*.json ./
RUN npm install

# 소스 코드 복사
COPY . .

# 프로덕션 빌드 실행
RUN npm run build

# --- 2. Production Stage ---
FROM nginx:stable-alpine

# Nginx 기본 설정 파일 삭제
RUN rm /etc/nginx/conf.d/default.conf

# 직접 작성한 Nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/conf.d/

# 빌드된 정적 파일들을 Nginx 웹서버 디렉토리로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 80 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
