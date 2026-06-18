// Package store 负责任务状态的持久化。
// 默认使用 MySQL;DSN 为空时降级为内存实现(便于本地开发与测试)。
package store

import (
	"database/sql"
	"fmt"

	_ "github.com/go-sql-driver/mysql"
)

// Status 对应 proto.TaskStatusEnum 的数值。
// 0=UNSPECIFIED, 1=RUNNING, 2=SUCCEEDED, 3=FAILED
type Status int

const (
	StatusUnspecified Status = 0
	StatusRunning     Status = 1
	StatusSucceeded   Status = 2
	StatusFailed      Status = 3
)

// Task 是任务在持久层的表示。
type Task struct {
	TaskID   string
	TaskType int
	Payload  string
	Status   Status
	Result   string
}

// Store 抽象任务存储。executor 仅依赖此接口,便于单测替换。
type Store interface {
	// Save 插入或更新一条任务记录。
	Save(t *Task) error
	// Get 按 task_id 查询。找不到时返回 (nil, false, nil)。
	Get(taskID string) (*Task, bool, error)
	// Close 释放底层资源。
	Close() error
}

// Open 按 DSN 选择实现。dsn 为空返回内存 store。
func Open(dsn string) (Store, error) {
	if dsn == "" {
		return NewMemory(), nil
	}
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, fmt.Errorf("打开 MySQL 失败: %w", err)
	}
	// gRPC 端口监听前先确认连通,失败快速暴露。
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("MySQL ping 失败: %w", err)
	}
	return &mysqlStore{db: db}, nil
}
