FROM golang:1.24-alpine AS builder

WORKDIR /repo

ENV GOPROXY=https://goproxy.cn,direct

# alpine 换国内源加速 apk
RUN sed -i 's|dl-cdn.alpinelinux.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apk/repositories

# 复制源码与 proto 定义(context 是仓库根)
COPY worker-service ./worker-service
COPY protos ./protos

WORKDIR /repo/worker-service

# proto 产物由 scripts/gen_proto.sh 在本地生成并随源码 COPY 进来,
# 避免镜像内安装重型 protoc/apk protobuf(那会拖入 100+ abseil 依赖,极慢)。
RUN test -f proto/worker.pb.go && test -f proto/worker_grpc.pb.go || \
    { echo "❌ proto 产物缺失,请在仓库根运行 bash scripts/gen_proto.sh 生成后重新构建"; exit 1; }

# 解析依赖(生成 go.sum 并下载)
RUN go mod tidy

# 编译
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/main ./cmd/main.go

FROM alpine:latest
RUN sed -i 's|dl-cdn.alpinelinux.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apk/repositories && \
    apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /out/main .
EXPOSE 50051
CMD ["./main"]
