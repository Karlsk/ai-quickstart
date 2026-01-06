from typing import List, Dict

# Memory：回合记忆
# - items：统一存储“用户/助手/环境”等事件，形成对话历史
# - 通过 get_memories 提供最近N条消息给提示构造使用
# - 通过 copy_without_system_memories 可过滤掉系统消息（某些场景需要）
class Memory:
    def __init__(self):
        self.items = []  # Basic conversation history

    def add_memory(self, memory: dict):
        """将一条记忆事件追加到工作记忆，用于后续提示词构造与推理"""
        self.items.append(memory)

    def get_memories(self, limit: int = None) -> List[Dict]:
        """获取用于提示词的对话历史；可通过 limit 限制条数以控制上下文长度"""
        return self.items[:limit]

    def copy_without_system_memories(self):
        """返回一份不包含系统类型（type==system）记忆的副本，用于部分提示场景"""
        filtered_items = [m for m in self.items if m["type"] != "system"]
        memory = Memory()
        memory.items = filtered_items
        return memory
