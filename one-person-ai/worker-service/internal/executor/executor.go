package executor

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/onepersonai/worker/internal/llm"
	pb "github.com/onepersonai/worker/proto"
)

// taskStatus 内部任务状态记录。MVP 用内存 map 存储,重启丢失。
// 多实例/持久化需求时替换为 MySQL(已引入 gorm,可平滑迁移)。
type taskStatus struct {
	status pb.TaskStatusEnum
	result string
}

// Executor 维护任务队列与状态。
type Executor struct {
	llm    *llm.Client
	mu     sync.RWMutex
	tasks  map[string]*taskStatus
	nextID int
}

func New(llmClient *llm.Client) *Executor {
	return &Executor{
		llm:   llmClient,
		tasks: make(map[string]*taskStatus),
	}
}

// Submit 接收任务并入队执行,立即返回 task_id。
// 执行是异步的(goroutine),通过 GetStatus 轮询结果。
func (e *Executor) Submit(taskType pb.TaskType, payload string) string {
	e.mu.Lock()
	e.nextID++
	taskID := fmt.Sprintf("task-%d-%d", e.nextID, time.Now().UnixNano())
	e.tasks[taskID] = &taskStatus{status: pb.TaskStatusEnum_RUNNING}
	e.mu.Unlock()

	go e.run(taskID, taskType, payload)
	return taskID
}

// Get 查询任务状态。
func (e *Executor) Get(taskID string) (pb.TaskStatusEnum, string, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	t, ok := e.tasks[taskID]
	if !ok {
		return pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED, "", false
	}
	return t.status, t.result, true
}

func (e *Executor) run(taskID string, taskType pb.TaskType, payload string) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[executor] task %s panic: %v", taskID, r)
			e.setResult(taskID, pb.TaskStatusEnum_FAILED, fmt.Sprintf("内部错误: %v", r))
		}
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()

	switch taskType {
	case pb.TaskType_LLM_CALL:
		e.handleLLMCall(ctx, taskID, payload)
	case pb.TaskType_PR_REVIEW:
		// Phase 2 实现
		e.setResult(taskID, pb.TaskStatusEnum_FAILED, "PR_REVIEW 尚未实现")
	default:
		e.setResult(taskID, pb.TaskStatusEnum_FAILED, fmt.Sprintf("未知任务类型: %v", taskType))
	}
}

// llmCallPayload 与 Python 侧约定的 JSON 负载格式。
type llmCallPayload struct {
	Prompt       string        `json:"prompt"`
	SystemPrompt string        `json:"system_prompt"`
	Messages     []llm.Message `json:"messages,omitempty"`
	MaxTokens    int           `json:"max_tokens,omitempty"`
	Temperature  float64       `json:"temperature,omitempty"`
}

func (e *Executor) handleLLMCall(ctx context.Context, taskID, payloadJSON string) {
	var p llmCallPayload
	if err := json.Unmarshal([]byte(payloadJSON), &p); err != nil {
		e.setResult(taskID, pb.TaskStatusEnum_FAILED, fmt.Sprintf("解析负载失败: %v", err))
		return
	}

	// 组装 messages:优先用显式传入的 messages,否则从 prompt+system 构造
	msgs := p.Messages
	if len(msgs) == 0 {
		if p.Prompt == "" {
			e.setResult(taskID, pb.TaskStatusEnum_FAILED, "prompt 和 messages 至少需要一个")
			return
		}
		msgs = make([]llm.Message, 0, 2)
		if p.SystemPrompt != "" {
			msgs = append(msgs, llm.Message{Role: "system", Content: p.SystemPrompt})
		}
		msgs = append(msgs, llm.Message{Role: "user", Content: p.Prompt})
	}

	maxTok := p.MaxTokens
	if maxTok == 0 {
		maxTok = 2000
	}
	temp := p.Temperature
	if temp == 0 {
		temp = 0.7
	}

	out, err := e.llm.Chat(ctx, msgs, maxTok, temp)
	if err != nil {
		e.setResult(taskID, pb.TaskStatusEnum_FAILED, err.Error())
		return
	}
	e.setResult(taskID, pb.TaskStatusEnum_SUCCEEDED, out)
}

func (e *Executor) setResult(taskID string, status pb.TaskStatusEnum, result string) {
	e.mu.Lock()
	defer e.mu.Unlock()
	if t, ok := e.tasks[taskID]; ok {
		t.status = status
		t.result = result
	}
}
