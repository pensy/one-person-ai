FROM python:3.11-slim

WORKDIR /app

# 换国内 apt 源(腾讯云内网 Debian 源,加速 apt update/install)
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null; \
    true

# 系统依赖
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# Python 依赖(含 grpcio-tools),pip 用国内源加速
COPY api-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 先复制应用源码(含 protos/ 已生成的 Python gRPC stub,由 scripts/gen_proto.sh 本地生成)
COPY api-service ./api-service

# 校验 proto 产物存在(避免缺失导致运行时 import 失败)
RUN test -f api-service/protos/worker_pb2.py && test -f api-service/protos/worker_pb2_grpc.py || \
    { echo "❌ proto 产物缺失,请在仓库根运行 bash scripts/gen_proto.sh 生成后重新构建"; exit 1; }

WORKDIR /app/api-service

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
