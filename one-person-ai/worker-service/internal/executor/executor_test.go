package executor

import (
	"testing"

	"github.com/onepersonai/worker/internal/store"
	pb "github.com/onepersonai/worker/proto"
)

func TestPbStoreStatusRoundTrip(t *testing.T) {
	cases := []pb.TaskStatusEnum{
		pb.TaskStatusEnum_RUNNING,
		pb.TaskStatusEnum_SUCCEEDED,
		pb.TaskStatusEnum_FAILED,
		pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED,
	}
	for _, s := range cases {
		got := storeToPBStatus(pbToStoreStatus(s))
		if got != s {
			t.Errorf("round trip %v -> %v -> %v", s, pbToStoreStatus(s), got)
		}
	}
}

func TestMemoryStoreSaveGet(t *testing.T) {
	s := store.NewMemory()
	task := &store.Task{
		TaskID:   "task-test-1",
		TaskType: int(pb.TaskType_LLM_CALL),
		Payload:  `{"prompt":"hi"}`,
		Status:   store.StatusRunning,
	}
	if err := s.Save(task); err != nil {
		t.Fatalf("Save: %v", err)
	}
	got, ok, err := s.Get("task-test-1")
	if err != nil || !ok {
		t.Fatalf("Get: ok=%v err=%v", ok, err)
	}
	if got.Status != store.StatusRunning || got.Payload != `{"prompt":"hi"}` {
		t.Errorf("unexpected task: %+v", got)
	}
	// 更新状态后应覆盖
	task.Status = store.StatusSucceeded
	task.Result = "done"
	if err := s.Save(task); err != nil {
		t.Fatalf("Save update: %v", err)
	}
	got, _, _ = s.Get("task-test-1")
	if got.Status != store.StatusSucceeded || got.Result != "done" {
		t.Errorf("update not persisted: %+v", got)
	}
	// 查不到的任务
	_, ok, _ = s.Get("not-exist")
	if ok {
		t.Error("expected ok=false for missing task")
	}
}
