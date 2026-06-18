package store

import "sync"

// memoryStore 内存实现,DSN 为空时使用。重启丢失,仅用于本地开发/测试。
type memoryStore struct {
	mu    sync.RWMutex
	tasks map[string]*Task
}

func NewMemory() Store {
	return &memoryStore{tasks: make(map[string]*Task)}
}

func (m *memoryStore) Save(t *Task) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	// 复制一份,避免外部修改影响内部状态
	cp := *t
	m.tasks[t.TaskID] = &cp
	return nil
}

func (m *memoryStore) Get(taskID string) (*Task, bool, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	t, ok := m.tasks[taskID]
	if !ok {
		return nil, false, nil
	}
	cp := *t
	return &cp, true, nil
}

func (m *memoryStore) Close() error { return nil }
