package executor

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/onepersonai/worker/internal/llm"
	"github.com/onepersonai/worker/internal/store"
	pb "github.com/onepersonai/worker/proto"
)

// pbToStoreStatus 把 proto 状态映射到 store 状态。
func pbToStoreStatus(s pb.TaskStatusEnum) store.Status {
	switch s {
	case pb.TaskStatusEnum_RUNNING:
		return store.StatusRunning
	case pb.TaskStatusEnum_SUCCEEDED:
		return store.StatusSucceeded
	case pb.TaskStatusEnum_FAILED:
		return store.StatusFailed
	default:
		return store.StatusUnspecified
	}
}

// storeToPBStatus 反向映射。
func storeToPBStatus(s store.Status) pb.TaskStatusEnum {
	switch s {
	case store.StatusRunning:
		return pb.TaskStatusEnum_RUNNING
	case store.StatusSucceeded:
		return pb.TaskStatusEnum_SUCCEEDED
	case store.StatusFailed:
		return pb.TaskStatusEnum_FAILED
	default:
		return pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED
	}
}

// Executor 维护任务队列与状态。状态持久化由 store.Store 负责
// (MySQL 或内存),重启不丢失(配置了 DSN 时)。
type Executor struct {
	llm   *llm.Client
	store store.Store
}

func New(llmClient *llm.Client, s store.Store) *Executor {
	return &Executor{llm: llmClient, store: s}
}

// Submit 接收任务并入队执行,立即返回 task_id。
// 执行是异步的(goroutine),通过 GetStatus 轮询结果。
func (e *Executor) Submit(taskType pb.TaskType, payload string) string {
	// 单调自增 + 纳秒,避免多实例/重启冲突
	taskID := fmt.Sprintf("task-%d", time.Now().UnixNano())

	task := &store.Task{
		TaskID:   taskID,
		TaskType: int(taskType),
		Payload:  payload,
		Status:   store.StatusRunning,
	}
	if err := e.store.Save(task); err != nil {
		log.Printf("[executor] 保存任务初始状态失败 task=%s: %v", taskID, err)
		// 仍继续执行,内存模式下 Get 也能拿到(若 store 是 memory)
	}

	go e.run(taskID, taskType, payload)
	return taskID
}

// Get 查询任务状态。
func (e *Executor) Get(taskID string) (pb.TaskStatusEnum, string, bool) {
	t, ok, err := e.store.Get(taskID)
	if err != nil {
		log.Printf("[executor] 查询任务失败 task=%s: %v", taskID, err)
		return pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED, "", false
	}
	if !ok {
		return pb.TaskStatusEnum_TASK_STATUS_UNSPECIFIED, "", false
	}
	return storeToPBStatus(t.Status), t.Result, true
}

func (e *Executor) run(taskID string, taskType pb.TaskType, payload string) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[executor] task %s panic: %v", taskID, r)
			e.setResult(taskID, taskType, payload, pb.TaskStatusEnum_FAILED, fmt.Sprintf("内部错误: %v", r))
		}
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()

	switch taskType {
	case pb.TaskType_LLM_CALL:
		e.handleLLMCall(ctx, taskID, taskType, payload)
	case pb.TaskType_PR_REVIEW:
		e.handlePRReview(ctx, taskID, taskType, payload)
	default:
		e.setResult(taskID, taskType, payload, pb.TaskStatusEnum_FAILED, fmt.Sprintf("未知任务类型: %v", taskType))
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

func (e *Executor) handleLLMCall(ctx context.Context, taskID string, taskType pb.TaskType, payloadJSON string) {
	var p llmCallPayload
	if err := json.Unmarshal([]byte(payloadJSON), &p); err != nil {
		e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, fmt.Sprintf("解析负载失败: %v", err))
		return
	}

	// 组装 messages:优先用显式传入的 messages,否则从 prompt+system 构造
	msgs := p.Messages
	if len(msgs) == 0 {
		if p.Prompt == "" {
			e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, "prompt 和 messages 至少需要一个")
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
		e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, err.Error())
		return
	}
	e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_SUCCEEDED, out)
}

// prReviewPayload 与 Python 侧约定的 PR_REVIEW 负载格式(proto 注释已定义)。
// API 侧负责用 PAT 拉取 diff,worker 只做 LLM 审查。
type prReviewPayload struct {
	Diff      string `json:"diff"`
	Repo      string `json:"repo"`
	PRNumber  int    `json:"pr_number"`
}

// PR_REVIEW 审查系统提示:资深审查专家,关注 bug/安全/性能/可读性。
const prReviewSystemPrompt = `你是一个资深代码审查专家。请审查给出的 GitHub PR diff,从以下角度给出意见:
1) 潜在 Bug 或逻辑错误
2) 安全问题(注入、越权、敏感信息泄露等)
3) 性能问题
4) 可读性与代码规范
5) 改进建议(给出具体示例)
用中文回答,Markdown 格式,条理清晰。如果 diff 中有值得肯定的地方也简要提及。`

// diff 审查的输入上限(字符),超出截断防 LLM 超长。
const maxDiffChars = 50000

func (e *Executor) handlePRReview(ctx context.Context, taskID string, taskType pb.TaskType, payloadJSON string) {
	var p prReviewPayload
	if err := json.Unmarshal([]byte(payloadJSON), &p); err != nil {
		e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, fmt.Sprintf("解析负载失败: %v", err))
		return
	}
	if p.Diff == "" {
		e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, "diff 为空")
		return
	}

	// 截断过长 diff(MVP 不分块,直接截断尾部)
	diff := p.Diff
	if len(diff) > maxDiffChars {
		diff = diff[:maxDiffChars] + "\n\n... (diff 过长,已截断,仅审查前 " + fmt.Sprintf("%d", maxDiffChars) + " 字符)"
	}

	msgs := []llm.Message{
		{Role: "system", Content: prReviewSystemPrompt},
		{Role: "user", Content: fmt.Sprintf("请审查以下 PR diff(仓库: %s, PR #%d):\n\n```diff\n%s\n```", p.Repo, p.PRNumber, diff)},
	}

	// 审查用低温度求稳定,token 上限放宽到 3000
	out, err := e.llm.Chat(ctx, msgs, 3000, 0.3)
	if err != nil {
		e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_FAILED, err.Error())
		return
	}
	e.setResult(taskID, taskType, payloadJSON, pb.TaskStatusEnum_SUCCEEDED, out)
}

func (e *Executor) setResult(taskID string, taskType pb.TaskType, payload string, status pb.TaskStatusEnum, result string) {
	task := &store.Task{
		TaskID:   taskID,
		TaskType: int(taskType),
		Payload:  payload,
		Status:   pbToStoreStatus(status),
		Result:   result,
	}
	if err := e.store.Save(task); err != nil {
		log.Printf("[executor] 保存任务结果失败 task=%s: %v", taskID, err)
	}
}
