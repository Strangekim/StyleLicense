# 1. NVIDIA CUDA 런타임 이미지를 베이스로 사용
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# 2. Python 및 필수 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3-venv \
    && \
    rm -rf /var/lib/apt/lists/*

# 3. Python 3.11을 기본 python으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 애플리케이션 코드 복사
COPY . .

# 7. 애플리케이션 실행
CMD ["python", "main.py"]
