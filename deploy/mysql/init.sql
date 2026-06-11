-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    credits INT NOT NULL DEFAULT 100 COMMENT '用户积分余额',
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 工具表
CREATE TABLE IF NOT EXISTS tools (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '工具名称',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '工具描述',
    category VARCHAR(30) NOT NULL COMMENT '分类: code, text, image, data',
    credits_cost INT NOT NULL DEFAULT 1 COMMENT '单次调用消耗积分',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI工具表';

-- 调用记录表
CREATE TABLE IF NOT EXISTS tool_calls (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    tool_id BIGINT NOT NULL,
    credits_used INT NOT NULL,
    input_text TEXT COMMENT '输入内容（脱敏存储）',
    output_text TEXT COMMENT '输出内容（脱敏存储）',
    status ENUM('success', 'failed', 'pending') NOT NULL DEFAULT 'pending',
    error_msg TEXT COMMENT '失败原因',
    ip_address VARCHAR(45) COMMENT 'IPv4/IPv6',
    user_agent TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE,
    INDEX idx_user_tool (user_id, tool_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具调用记录表';

-- 积分消费记录表
CREATE TABLE IF NOT EXISTS credit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    change_amount INT NOT NULL COMMENT '正数为增加，负数为扣减',
    balance_after INT NOT NULL COMMENT '变动后余额',
    reason VARCHAR(200) NOT NULL COMMENT '变动原因',
    related_call_id BIGINT NULL COMMENT '关联调用记录ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='积分变动记录表';

-- 插入初始工具数据
INSERT INTO tools (name, display_name, description, category, credits_cost) VALUES
('code_explain', '代码解释器', '输入代码，AI 帮你解释逻辑和潜在问题', 'code', 1),
('code_review', '代码审查', '对代码进行专业审查，给出改进建议', 'code', 2),
('text_polish', '文本润色', '优化文章表达，让文字更流畅专业', 'text', 1),
('text_summary', '内容摘要', '长文自动摘要，快速获取核心信息', 'text', 1)
ON DUPLICATE KEY UPDATE display_name=VALUES(display_name);
