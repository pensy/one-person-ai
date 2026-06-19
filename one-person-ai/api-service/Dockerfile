FROM python:3.11-slim

WORKDIR /app

# 系统依赖(protobuf-compiler 备用,实际用 grpcio-tools 生成)
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# Python 依赖(含 grpcio-tools)
COPY api-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 先复制应用源码(含 protos/ 已生成的 Python gRPC stub,由 scripts/gen_proto.sh 本地生成)
COPY api-service ./api-service

# 校验 proto 产物存在(避免缺失导致运行时 import 失败)
RUN test -f api-service/protos/worker_pb2.py && test -f api-service/protos/worker_pb2_grpc.py || \
    { echo "❌ proto 产物缺失,请在仓库根运行 bash scripts/gen_proto.sh 生成后重新构建"; exit 1; }

WORKDIR /app/api-service

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
