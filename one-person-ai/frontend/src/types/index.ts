// 共享类型定义

export interface User {
  id: number;
  username: string;
  email: string;
  credits: number;
  role: "user" | "admin";
  created_at: string;
}

export interface Tool {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  category: string;
  credits_cost: number;
}

export interface ToolCall {
  id: number;
  user_id: number;
  tool_id: number;
  credits_used: number;
  input_text: string | null;
  output_text: string | null;
  status: "success" | "failed" | "pending";
  error_msg: string | null;
  created_at: string;
}

// API 统一错误格式(FastAPI HTTPException 的 detail 字段)
export interface ApiError {
  detail: string;
}
