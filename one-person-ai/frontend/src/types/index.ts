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
  is_active?: boolean;
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

// 工作流(Phase 1)
export interface WorkflowStep {
  tool: string;
  label: string;
}

export interface Workflow {
  name: string;
  display_name: string;
  description: string;
  steps: WorkflowStep[];
  credits_cost: number;
}

export interface WorkflowStepResult {
  label: string;
  tool: string;
  status: "success" | "failed";
  output: string | null;
  error: string | null;
}

export interface WorkflowRunResponse {
  id: number;
  status: "success" | "failed";
  steps: WorkflowStepResult[];
  credits_used: number;
}

// PR 审查(Phase 2)
export interface PRReviewRequest {
  repo: string;
  pr_number: number;
  github_token: string;
}

// 管理后台
export interface AdminStatusCheck {
  status: string;
  version?: string;
  message?: string;
}

export interface AdminStatus {
  api: AdminStatusCheck;
  mysql: AdminStatusCheck;
  worker: AdminStatusCheck;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  credits: number;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface PRReviewResponse {
  id: number;
  status: "success" | "failed";
  output_text: string | null;
  credits_used: number;
}
