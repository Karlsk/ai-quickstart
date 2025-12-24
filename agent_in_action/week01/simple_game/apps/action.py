from typing import Callable, Dict, Any, List


# Action：动作/工具的抽象
# - name：动作名（作为工具名暴露给 LLM）
# - function：实际执行的 Python 函数
# - description：工具说明，帮助 LLM 选择正确工具
# - parameters：JSON Schema（决定 LLM 该如何拼好参数）
# - terminal：是否为“终止型”动作（被选中后终止主循环）
class Action:
    def __init__(
            self,
            name: str,
            function: Callable,
            description: str,
            parameters: Dict[str, Any],
            terminal: bool = False,
    ):
        self.name = name
        self.function = function
        self.description = description
        self.parameters = parameters
        self.terminal = terminal

    def execute(self, **args) -> Any:
        return self.function(**args)


# ActionRegistry：动作/工具注册表
# - 负责集中管理动作/工具对象，支持按名称检索与批量导出供 AgentLanguage 生成工具Schema
class ActionRegistry:
    def __init__(self):
        self.actions = {}

    def register(self, action: Action):
        self.actions[action.name] = action

    def get_action(self, name: str) -> [Action, None]:
        return self.actions.get(name, None)

    def get_actions(self) -> List[Action]:
        """获取所有已注册的动作，按注册顺序返回列表"""
        return list(self.actions.values())
