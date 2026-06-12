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
    system = (
        "你是一个资深代码审查专家。请对给出的代码进行详细解释，包括："
        "1) 代码逻辑和功能 "
        "2) 潜在问题或改进建议 "
        "3) 时间/空间复杂度分析（如适用）。"
        "用中文回答，简洁清晰。"
    )
    return call_deepseek(f"请解释以下代码：\n\n```\n{code}\n```", system_prompt=system)


def review_code(code: str) -> str:
    system = (
        "你是一个资深代码审查专家。请从以下角度审查代码："
        "1) 代码质量和可读性 "
        "2) 潜在 Bug 或边界问题 "
        "3) 性能优化建议 "
        "4) 最佳实践建议。"
        "用中文回答，条理清晰，给出具体改进示例。"
    )
    return call_deepseek(f"请审查以下代码：\n\n```\n{code}\n```", system_prompt=system)


def polish_text(text: str) -> str:
    system = (
        "你是一个专业的文字编辑。请对给出的文本进行润色，使其更流畅、专业、易读。"
        "保持原意不变，只优化表达。直接输出润色后的文本，不要加解释。"
    )
    return call_deepseek(f"请润色以下文本：\n\n{text}", system_prompt=system)


def summarize_text(text: str) -> str:
    system = (
        "你是一个专业的文本摘要助手。请用简洁的中文概括以下文本的核心内容，"
        "控制在200字以内，分点列出关键信息。"
    )
    return call_deepseek(f"请摘要以下内容：\n\n{text}", system_prompt=system)


def sql_generate(requirement: str) -> str:
    """自然语言转 SQL"""
    system = (
        "你是一个资深数据库专家。用户会用自然语言描述数据查询需求，"
        "请生成对应的 SQL 语句。要求："
        "1) 默认生成 MySQL 语法 "
        "2) 每条 SQL 后加简短注释说明作用 "
        "3) 如果需求不明确，列出可能的几种写法 "
        "4) 涉及多表时，说明表关联逻辑。"
        "用中文回答，格式清晰。"
    )
    return call_deepseek(
        f"请根据以下需求生成 SQL：\n\n{requirement}",
        system_prompt=system,
        max_tokens=3000,
    )


def regex_generate(description: str) -> str:
    """自然语言转正则表达式"""
    system = (
        "你是一个正则表达式专家。用户会用自然语言描述文本匹配需求，"
        "请生成对应的正则表达式。要求："
        "1) 给出正则表达式本身 "
        "2) 逐段解释正则的含义 "
        "3) 给出 2-3 个匹配/不匹配的示例 "
        "4) 指出可能的边界情况。"
        "用中文回答，格式清晰。"
    )
    return call_deepseek(
        f"请根据以下描述生成正则表达式：\n\n{description}",
        system_prompt=system,
    )


def api_doc(code: str) -> str:
    """从代码生成 API 文档"""
    system = (
        "你是一个专业的 API 文档撰写专家。请根据给出的代码，"
        "生成规范的 API 接口文档。要求："
        "1) 接口路径和方法 "
        "2) 请求参数说明（参数名、类型、必填、说明）"
        "3) 响应格式和字段说明 "
        "4) 请求示例和响应示例 "
        "5) 可能的错误码说明。"
        "用 Markdown 格式输出，中文说明。"
    )
    return call_deepseek(
        f"请为以下代码生成 API 文档：\n\n```\n{code}\n```",
        system_prompt=system,
        max_tokens=3000,
    )


def json_format(json_str: str) -> str:
    """JSON 格式化和结构分析"""
    system = (
        "你是一个数据处理专家。请对给出的 JSON 进行："
        "1) 格式化输出（美化排版）"
        "2) 分析 JSON 结构，列出所有字段及其类型"
        "3) 给出字段的中文含义推测"
        "4) 如有嵌套结构，画出层级关系。"
        "用中文回答，格式清晰。"
    )
    return call_deepseek(
        f"请分析以下 JSON：\n\n```json\n{json_str}\n```",
        system_prompt=system,
    )
