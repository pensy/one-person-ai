package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Message 兼容 OpenAI ChatCompletion 格式。
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// Client 封装对 DeepSeek(OpenAI 兼容)接口的调用。
type Client struct {
	apiKey   string
	baseURL  string
	model    string
	httpCli  *http.Client
}

func New(apiKey, baseURL, model string) *Client {
	return &Client{
		apiKey:  apiKey,
		baseURL: baseURL,
		model:   model,
		httpCli: &http.Client{Timeout: 120 * time.Second},
	}
}

type chatRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Temperature float64   `json:"temperature,omitempty"`
}

type chatResponse struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

// Chat 发起一次对话。messages 至少含一条。
func (c *Client) Chat(ctx context.Context, messages []Message, maxTokens int, temperature float64) (string, error) {
	if len(messages) == 0 {
		return "", fmt.Errorf("messages 不能为空")
	}

	body, err := json.Marshal(chatRequest{
		Model:       c.model,
		Messages:    messages,
		MaxTokens:   maxTokens,
		Temperature: temperature,
	})
	if err != nil {
		return "", fmt.Errorf("序列化请求失败: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("创建请求失败: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.apiKey)

	resp, err := c.httpCli.Do(req)
	if err != nil {
		return "", fmt.Errorf("调用 LLM 失败: %w", err)
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取响应失败: %w", err)
	}

	var result chatResponse
	if err := json.Unmarshal(raw, &result); err != nil {
		return "", fmt.Errorf("解析响应失败: %w, body=%s", err, string(raw))
	}
	if result.Error != nil {
		return "", fmt.Errorf("LLM 返回错误: %s", result.Error.Message)
	}
	if len(result.Choices) == 0 {
		return "", fmt.Errorf("LLM 返回空结果")
	}
	return result.Choices[0].Message.Content, nil
}
