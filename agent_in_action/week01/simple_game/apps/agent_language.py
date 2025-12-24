from typing import List, Any
import json

from .llm import Prompt
from .action import Action
from .environment import Environment
from .memory import Memory
from .goal import Goal


# AgentLanguage：语言适配层
# - 负责把（Goals/Actions/Memory）格式化为 LLM 需要的 Prompt
# - 负责从 LLM 的原始输出中解析出“要调用的工具与参数”
class AgentLanguage:
    def __init__(self):
        pass

    def construct_prompt(
            self,
            actions: List[Action],
            environment: Environment,
            goals: List[Goal],
            memory: Memory
    ) -> Prompt:
        raise NotImplementedError("Subclasses must implement this method")

    def parse_response(self, response: str) -> dict:
        raise NotImplementedError("Subclasses must implement this method")


# AgentFunctionCallingActionLanguage：基于“函数调用”范式的语言适配实现
# - 将 Goals 拼接为 system 消息
# - 将 Memory 规范化映射为 user/assistant 消息
# - 将 Actions 转换为符合 OpenAI 函数调用的 tools Schema
class AgentFunctionCallingActionLanguage(AgentLanguage):
    def __init__(self):
        super().__init__()

    @staticmethod
    def format_goals(goals: List[Goal]) -> List:
        # 把所有目标拼接为一个 system 消息，便于集中表达“要做什么/如何做”
        sep = "\n-------------------\n"
        goal_instructions = "\n\n".join([f"{goal.name}:{sep}{goal.description}{sep}" for goal in goals])
        return [
            {"role": "system", "content": goal_instructions}
        ]

    @staticmethod
    def format_memory(memory: Memory) -> List:
        """将 Memory 转换为对话消息格式，供 LLM 上下文使用"""
        # 记忆格式化策略：
        # - environment 的输出也作为 assistant 角色加入（让模型能“看到”工具执行结果）
        # - user/assistant 原样映射
        items = memory.get_memories()
        mapped_items = []
        for item in items:
            content = item.get("content", None)
            if not content:
                content = json.dumps(item, indent=4)

            if item["type"] == "assistant":
                mapped_items.append({"role": "assistant", "content": content})
            elif item["type"] == "environment":
                mapped_items.append({"role": "assistant", "content": content})
            else:
                mapped_items.append({"role": "user", "content": content})

        return mapped_items

    @staticmethod
    def format_actions(actions: List[Action]) -> [List, List]:
        """将已注册的动作转换为 OpenAI 函数调用所需的 tools Schema"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": action.name,
                    # 描述过长可能无效，限制到 1024 字符
                    "description": action.description[:1024],
                    "parameters": action.parameters,
                },
            } for action in actions
        ]

        return tools

    def construct_prompt(
            self,
            actions: List[Action],
            environment: Environment,
            goals: List[Goal],
            memory: Memory
    ) -> Prompt:
        # 构造最终 Prompt：Goals（system）+ Memory（历史消息）+ Tools（函数Schema）
        prompt = []
        prompt += self.format_goals(goals)
        prompt += self.format_memory(memory)

        tools = self.format_actions(actions)

        return Prompt(messages=prompt, tools=tools)

    def adapt_prompt_after_parsing_error(self,
                                         prompt: Prompt,
                                         response: str,
                                         traceback: str,
                                         error: Any,
                                         retries_left: int) -> Prompt:
        # 解析失败后的“自适应 Prompt”策略（此处保留扩展点，演示版不做修改）
        return prompt

    def parse_response(self, response: str) -> dict:
        """将 LLM 的响应解析为结构化格式（优先尝试 JSON 解析，失败则回退为终止工具）"""

        # 期望 LLM 返回 JSON 字符串：{"tool": 工具名, "args": {...}}
        try:
            return json.loads(response)

        except Exception as e:
            # 若无法解析，则将内容作为 message 交给终止工具，友好退出
            print(f"解析 LLM 响应失败，转为终止工具：{str(e)}")
            return {
                "tool": "terminate",
                "args": {"message": response}
            }
