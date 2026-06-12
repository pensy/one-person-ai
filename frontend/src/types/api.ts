// 后端 API 响应类型定义

export interface User {
  id: number;
  username: string;
  email: string;
  credits: number;
  role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Tool {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  category: string;
  credits_cost: number;
}

export interface ToolCallRequest {
  tool_name: string;
  input_text: string;
}

export interface ToolCallResponse {
  id: number;
  status: string;
  output_text: string | null;
  credits_used: number;
}
