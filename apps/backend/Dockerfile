# 1. Python 3.11-slim을 베이스 이미지로 사용
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 시스템 패키지 설치 (필요 시)
# 예: RUN apt-get update && apt-get install -y ...

# 4. Python 패키지 설치
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# 5. 애플리케이션 코드 복사
COPY . .

# 6. Gunicorn 실행
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi"]
