import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def get_deepseek_client() -> OpenAI:
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )


def call_deepseek(
    prompt: str,
    system_prompt: str = "你是一个有用的AI助手。",
    model: str = "deepseek-chat",
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """调用 DeepSeek API，返回响应文本"""
    client = get_deepseek_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def explain_code(code: str) -> str:
    """代码解释器"""
    system = "你是一个资深代码审查专家。请对给出的代码进行详细解释，包括：1) 代码逻辑和功能 2) 潜在问题或改进建议 3) 时间/空间复杂度分析（如适用）。用中文回答，简洁清晰。"
    return call_deepseek(f"请解释以下代码：\n\n```\n{code}\n```", system_prompt=system)


def review_code(code: str) -> str:
    """代码审查"""
    system = "你是一个资深代码审查专家。请从以下角度审查代码：1) 代码质量和可读性 2) 潜在 Bug 或边界问题 3) 性能优化建议 4) 最佳实践建议。用中文回答，条理清晰，给出具体改进示例。"
    return call_deepseek(f"请审查以下代码：\n\n```\n{code}\n```", system_prompt=system)


def polish_text(text: str) -> str:
    """文本润色"""
    system = "你是一个专业的文字编辑。请对给出的文本进行润色，使其更流畅、专业、易读。保持原意不变，只优化表达。直接输出润色后的文本，不要加解释。"
    return call_deepseek(f"请润色以下文本：\n\n{text}", system_prompt=system)


def summarize_text(text: str) -> str:
    """内容摘要"""
    system = "你是一个专业的文本摘要助手。请用简洁的中文概括以下文本的核心内容，控制在200字以内，分点列出关键信息。"
    return call_deepseek(f"请摘要以下内容：\n\n{text}", system_prompt=system)
