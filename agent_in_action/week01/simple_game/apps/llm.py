from openai import OpenAI  # 用于调用OpenAI API
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any
import os, json


# Prompt：封装要发给 LLM 的消息与工具定义
# - messages：对话上下文（系统/用户/助手三类）
# - tools：工具（函数）调用的 JSON Schema 描述（让 LLM 能“看见”可用的动作）
# - metadata：元数据（可选扩展，用 dict 保存）
@dataclass
class Prompt:
    messages: List[Dict] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

# 大语言模型
client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)


# generate_response：统一的 LLM 调用入口
# - 入参是 Prompt，内部自动根据是否提供 tools 来决定是否启用函数调用能力
# - 目标：把模型提供商与主循环解耦；将来切换模型时无需改 Agent 逻辑
# - 返回：
#   * 无工具时：直接返回助手文本
#   * 有工具时：优先解析 tool_calls（并转为 {tool, args} 的 JSON 字符串）
#               若无工具调用，则退化为普通文本回复
def generate_response(prompt: Prompt) -> str:
    messages = prompt.messages
    tools = prompt.tools

    if not tools:
        # 无工具：普通对话
        response = client.chat.completions.create(
            model="gpt-4o",  # 指定使用的模型
            messages=messages,  # 发送消息历史
            max_tokens=1024  # 限制响应长度
        )
        result = response.choices[0].message.content
    else:
        # 有工具：提示模型按函数调用格式返回 tool_calls
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            max_tokens=1024
        )
        if response.choices[0].message.tool_calls:
            # 这里仅取第一个工具调用作为最小可运行演示
            tool = response.choices[0].message.tool_calls[0]
            result = {
                "tool": tool.function.name,
                "args": json.loads(tool.function.arguments),
            }
            # 将 dict 序列化为字符串，便于统一处理与存入记忆
            result = json.dumps(result)

        else:
            result = response.choices[0].message.content

    return result
