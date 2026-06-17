package config

import "os"

// Config 从环境变量读取。Docker 部署时由 docker-compose 传入。
type Config struct {
	GRPCPort        string
	MySQLDSN        string
	DeepSeekAPIKey  string
	DeepSeekBaseURL string
	DeepSeekModel   string
}

// Load 从环境变量加载配置,带合理默认值。
func Load() *Config {
	return &Config{
		GRPCPort:        getEnv("GRPC_PORT", "50051"),
		MySQLDSN:        getEnv("DB_DSN", ""),
		DeepSeekAPIKey:  getEnv("DEEPSEEK_API_KEY", ""),
		DeepSeekBaseURL: getEnv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
		DeepSeekModel:   getEnv("DEEPSEEK_MODEL", "deepseek-chat"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
