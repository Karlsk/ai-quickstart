from typing import List, Callable
import json

from .llm import Prompt
from .action import ActionRegistry
from .environment import Environment
from .goal import Goal
from .agent_language import AgentLanguage
from .memory import Memory


# Agent：智能体主循环
# - 维护并协调 G/A/M/E（目标/动作/记忆/环境）
# - 统一的 prompt 构造、响应解析、动作执行、记忆更新、终止判断
class Agent:
    def __init__(self,
                 goals: List[Goal],
                 agent_language: AgentLanguage,
                 action_registry: ActionRegistry,
                 generate_response: Callable[[Prompt], str],
                 environment: Environment):
        """
        使用核心的 GAME 组件初始化智能体：
        - goals：目标与指令集合
        - agent_language：语言适配层（提示词构造与解析）
        - generate_response：LLM 调用函数
        - environment：动作执行环境
        """
        self.goals = goals
        self.generate_response = generate_response
        self.agent_language = agent_language
        self.actions = action_registry
        self.environment = environment

    def construct_prompt(self, goals: List[Goal], memory: Memory, actions: ActionRegistry) -> Prompt:
        """基于当前目标、记忆与动作集合构造提示词（Prompt）"""
        return self.agent_language.construct_prompt(
            actions=actions.get_actions(),
            environment=self.environment,
            goals=goals,
            memory=memory
        )

    def get_action(self, response):
        # 解析 LLM 的返回，得到动作名与参数（invocation）
        invocation = self.agent_language.parse_response(response)
        action = self.actions.get_action(invocation["tool"])
        return action, invocation

    def should_terminate(self, response: str) -> bool:
        # 若当前选择的动作被标记为 terminal，则结束主循环
        action_def, _ = self.get_action(response)
        return action_def.terminal

    @staticmethod
    def set_current_task(memory: Memory, task: str):
        # 将用户输入写入记忆，作为本轮起始任务语境
        memory.add_memory({"type": "user", "content": task})

    @staticmethod
    def update_memory(memory: Memory, response: str, result: dict):
        """
        使用“决策 + 执行结果”更新记忆：
        - 将助手的决策（response）作为 assistant 事件存入
        - 将环境执行结果（result）序列化为 JSON，作为 environment 事件存入
        """
        # 统一把“助手的决策（response）”与“环境执行结果（result）”写入记忆
        new_memories = [
            {"type": "assistant", "content": response},
            {"type": "environment", "content": json.dumps(result)}
        ]
        for m in new_memories:
            memory.add_memory(m)

    def prompt_llm_for_action(self, full_prompt: Prompt) -> str:
        # 将 Prompt 发送给 LLM，得到“下一步动作/或文本回复”
        response = self.generate_response(full_prompt)
        return response

    def run(self, user_input: str, memory=None, max_iterations: int = 50) -> Memory:
        """
        执行该智能体的 GAME 主循环，可设置最大迭代次数：
        - 每轮：构造 Prompt -> 让 LLM 决策 -> 解析动作 -> 环境执行 -> 写回记忆 -> 终止判断
        """
        if memory is None:
            memory = Memory()

        # 将用户输入作为当前任务写入记忆
        self.set_current_task(memory, user_input)

        for iteration in range(max_iterations):
            # 1) 用当前 Goals/Actions/Memory 构造 Prompt
            prompt = self.construct_prompt(self.goals, memory, self.actions)

            print("Agent thinking...")
            # 2) 发送给 LLM，得到“将要调用的动作及其参数”或普通文本
            response = self.prompt_llm_for_action(prompt)
            print(f"Agent Decision: {response}")

            # 解析 LLM 响应，得到动作定义与参数
            action, invocation = self.get_action(response)

            # 执行动作并获取结果
            result = self.environment.execute_action(action, invocation["args"])
            print(f"Action Result: {result}")

            # 5) 将“决策 + 结果”写回记忆，形成闭环
            self.update_memory(memory, response, result)

            # 6) 终止判断：如果动作为终止型，则跳出循环
            if self.should_terminate(response):
                break

        return memory

