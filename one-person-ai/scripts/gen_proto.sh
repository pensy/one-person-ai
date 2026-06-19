#!/usr/bin/env bash
# 从 protos/worker.proto 生成 Python 和 Go 的 gRPC 代码。
# 在仓库根目录运行:bash scripts/gen_proto.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROTO_FILE="$REPO_ROOT/protos/worker.proto"

if [ ! -f "$PROTO_FILE" ]; then
  echo "❌ 找不到 $PROTO_FILE" >&2
  exit 1
fi

echo "→ 生成 Python gRPC 代码 → api-service/protos/"
python3 -m grpc_tools.protoc \
  -I "$REPO_ROOT/protos" \
  --python_out="$REPO_ROOT/api-service/protos" \
  --grpc_python_out="$REPO_ROOT/api-service/protos" \
  "$PROTO_FILE"
touch "$REPO_ROOT/api-service/protos/__init__.py"
# 修正 import 路径:运行时包路径是 protos.worker_pb2
sed -i.bak 's/^import worker_pb2/from protos import worker_pb2/' "$REPO_ROOT/api-service/protos/worker_pb2_grpc.py" && rm -f "$REPO_ROOT/api-service/protos/worker_pb2_grpc.py.bak"
echo "✅ Python: api-service/protos/worker_pb2.py + worker_pb2_grpc.py"

echo ""
echo "→ 生成 Go gRPC 代码 → worker-service/proto/"
mkdir -p "$REPO_ROOT/worker-service/proto"
protoc \
  -I "$REPO_ROOT/protos" \
  --go_out="$REPO_ROOT/worker-service/proto" --go_opt=paths=source_relative \
  --go-grpc_out="$REPO_ROOT/worker-service/proto" --go-grpc_opt=paths=source_relative \
  "$PROTO_FILE"
# 写入最小 go.mod,使 replace 指令可解析
cat > "$REPO_ROOT/worker-service/proto/go.mod" << 'EOF'
module github.com/onepersonai/worker/proto

go 1.24
EOF
echo "✅ Go: worker-service/proto/worker.pb.go + worker_grpc.pb.go"

echo ""
echo "完成。生成产物已纳入版本控制,提交后即可用于 Docker 构建。"
