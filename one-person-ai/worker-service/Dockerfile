FROM golang:1.25-alpine AS builder

WORKDIR /repo

ENV GOPROXY=https://goproxy.cn,direct

# 系统依赖:protoc 编译器
RUN apk add --no-cache protobuf protobuf-dev

# Go 插件用于生成 gRPC 代码
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
ENV PATH="$PATH:/root/go/bin"

# 复制源码与 proto 定义(context 是仓库根)
COPY worker-service ./worker-service
COPY protos ./protos

WORKDIR /repo/worker-service

# 先生成 proto 代码(这样 go mod tidy/build 时 proto 包已存在)
RUN mkdir -p proto && \
    protoc -I /repo/protos \
      --go_out=proto --go_opt=paths=source_relative \
      --go-grpc_out=proto --go-grpc_opt=paths=source_relative \
      /repo/protos/worker.proto

# 解析依赖(生成 go.sum 并下载)
RUN go mod tidy

# 编译
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/main ./cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /out/main .
EXPOSE 50051
CMD ["./main"]
