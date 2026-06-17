FROM python:3.11-slim

WORKDIR /app

# 系统依赖(protobuf-compiler 备用,实际用 grpcio-tools 生成)
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# Python 依赖(含 grpcio-tools)
COPY api-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 先复制应用源码
COPY api-service ./api-service

# 生成 Python gRPC stub 到 api-service/protos/
# 生成后修正 import 路径:grpcio-tools 默认生成 `import worker_pb2`,
# 但运行时包路径是 `protos.worker_pb2`,需改写 grpc 文件里的 import。
COPY protos ./protos
RUN python -m grpc_tools.protoc \
      -I protos \
      --python_out=api-service/protos \
      --grpc_python_out=api-service/protos \
      protos/worker.proto && \
    touch api-service/protos/__init__.py && \
    sed -i 's/^import worker_pb2/from protos import worker_pb2/' api-service/protos/worker_pb2_grpc.py && \
    ls -la api-service/protos/

WORKDIR /app/api-service

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
