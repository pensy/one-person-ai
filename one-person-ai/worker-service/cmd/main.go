package main

import (
	"flag"
	"log"

	"github.com/onepersonai/worker/internal/config"
	"github.com/onepersonai/worker/internal/executor"
	"github.com/onepersonai/worker/internal/grpcserver"
	"github.com/onepersonai/worker/internal/llm"
)

func main() {
	cfg := config.Load()

	log.Println("One Person AI - Worker Service")
	log.Println("Version: 0.2.0")

	// 允许 --check 仅打印配置后退出(健康自检用)
	check := flag.Bool("check", false, "仅加载配置并退出,用于健康检查")
	flag.Parse()
	if *check {
		log.Printf("配置加载成功, gRPC 端口=%s", cfg.GRPCPort)
		return
	}

	// 初始化 LLM 客户端
	llmClient := llm.New(cfg.DeepSeekAPIKey, cfg.DeepSeekBaseURL, cfg.DeepSeekModel)
	if cfg.DeepSeekAPIKey == "" {
		log.Println("[WARN] DEEPSEEK_API_KEY 未设置,LLM 任务将失败")
	}

	// TODO: 初始化 MySQL 连接(持久化任务状态时启用)
	// 当前任务状态存内存,重启丢失

	// 启动 gRPC server(阻塞)
	exec := executor.New(llmClient)
	if err := grpcserver.Serve(cfg.GRPCPort, exec); err != nil {
		log.Fatalf("gRPC server 启动失败: %v", err)
	}
}
