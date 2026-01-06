from .action import Action

from typing import Dict, Any
import traceback
import time


# Environment：环境层（动作的真实执行者）
# - execute_action：捕获执行异常，统一返回结构（是否执行成功/错误/traceback/时间戳）
# - format_result：为成功结果补充元数据（时间戳），便于记录与日志化
class Environment:
    def execute_action(self, action: Action, args: Dict):
        """执行指定动作并返回标准化结果；捕获异常并提供错误与追踪信息"""
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def format_result(self, result: Any) -> Dict:
        """为执行结果补充元数据（如时间戳）并统一为标准结构"""
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }
