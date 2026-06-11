FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.34.0 \
    sqlalchemy==2.0.0 \
    pymysql==1.1.0 \
    pydantic==2.0.0 \
    python-jose==3.3.0 \
    passlib==1.7.4 \
    python-multipart==0.0.9 \
    openai==1.0.0 \
    python-dotenv==1.0.0 \
    bcrypt==4.0.0

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
