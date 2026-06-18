package main

import (
	"flag"
	"log"

	"github.com/onepersonai/worker/internal/config"
	"github.com/onepersonai/worker/internal/executor"
	"github.com/onepersonai/worker/internal/grpcserver"
	"github.com/onepersonai/worker/internal/llm"
	"github.com/onepersonai/worker/internal/store"
)

func main() {
	cfg := config.Load()

	log.Println("One Person AI - Worker Service")
	log.Println("Version: 0.3.0")

	// 允许 --check 仅打印配置后退出(健康自检用)
	check := flag.Bool("check", false, "仅加载配置并退出,用于健康检查")
	flag.Parse()
	if *check {
		log.Printf("配置加载成功, gRPC 端口=%s, MySQL DSN 已配置=%v", cfg.GRPCPort, cfg.MySQLDSN != "")
		return
	}

	// 初始化 LLM 客户端
	llmClient := llm.New(cfg.DeepSeekAPIKey, cfg.DeepSeekBaseURL, cfg.DeepSeekModel)
	if cfg.DeepSeekAPIKey == "" {
		log.Println("[WARN] DEEPSEEK_API_KEY 未设置,LLM 任务将失败")
	}

	// 初始化任务存储。DSN 为空时降级为内存模式(重启丢失,仅本地开发)。
	taskStore, err := store.Open(cfg.MySQLDSN)
	if err != nil {
		log.Fatalf("初始化任务存储失败: %v", err)
	}
	defer taskStore.Close()
	if cfg.MySQLDSN == "" {
		log.Println("[WARN] DB_DSN 未设置,任务状态仅存内存,重启丢失")
	} else {
		log.Println("[INFO] 任务状态持久化到 MySQL 已启用")
	}

	// 启动 gRPC server(阻塞)
	exec := executor.New(llmClient, taskStore)
	if err := grpcserver.Serve(cfg.GRPCPort, exec); err != nil {
		log.Fatalf("gRPC server 启动失败: %v", err)
	}
}
