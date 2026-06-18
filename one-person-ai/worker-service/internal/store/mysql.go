package store

import (
	"database/sql"
	"fmt"
)

// mysqlStore 基于 database/sql 的实现。
type mysqlStore struct {
	db *sql.DB
}

// Save 用 REPLACE INTO 兼容插入与更新(Save 调用前已知 task_id)。
func (s *mysqlStore) Save(t *Task) error {
	_, err := s.db.Exec(
		`REPLACE INTO worker_tasks (task_id, task_type, payload, status, result) VALUES (?, ?, ?, ?, ?)`,
		t.TaskID, t.TaskType, t.Payload, int(t.Status), t.Result,
	)
	if err != nil {
		return fmt.Errorf("写入 worker_tasks 失败: %w", err)
	}
	return nil
}

func (s *mysqlStore) Get(taskID string) (*Task, bool, error) {
	var t Task
	var status int
	err := s.db.QueryRow(
		`SELECT task_id, task_type, payload, status, result FROM worker_tasks WHERE task_id = ?`,
		taskID,
	).Scan(&t.TaskID, &t.TaskType, &t.Payload, &status, &t.Result)
	if err == sql.ErrNoRows {
		return nil, false, nil
	}
	if err != nil {
		return nil, false, fmt.Errorf("查询 worker_tasks 失败: %w", err)
	}
	t.Status = Status(status)
	return &t, true, nil
}

func (s *mysqlStore) Close() error { return s.db.Close() }
