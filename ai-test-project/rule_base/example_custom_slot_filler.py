"""
自定义槽位提取器示例

演示如何：
1. 创建自定义槽位提取器
2. 注册到 RuleEngine
3. 通过 context 指定使用特定的槽位提取器
"""

from pathlib import Path
from typing import Any, Dict
from intent_recognition.core.slot_filler import BaseSlotFiller
from intent_recognition.core.rule_engine import RuleEngine


class CustomSlotFiller(BaseSlotFiller):
    """
    自定义槽位提取器示例：
    - 可以实现特定领域的槽位提取逻辑
    - 例如：针对特定业务场景的槽位解析
    """

    def __init__(self, config, custom_param: str = "default"):
        super().__init__(name="custom_filler", priority=90)
        self.config = config
        self.custom_param = custom_param

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """
        自定义槽位填充逻辑
        """
        print(f"[CustomSlotFiller] Processing with param: {self.custom_param}")
        
        # 这里可以实现你的自定义逻辑
        # 例如：调用特定的API、使用特定的规则等
        
        # 示例：添加一个自定义槽位
        if intent_result.slots is None:
            intent_result.slots = {}
        
        intent_result.slots["processed_by"] = self.name
        intent_result.slots["custom_param"] = self.custom_param
        
        # 可以链式调用其他处理逻辑
        # ...
        
        return intent_result


class AdvancedSlotFiller(BaseSlotFiller):
    """
    高级槽位提取器示例：
    - 可以集成更复杂的逻辑，如调用大模型、外部API等
    """

    def __init__(self, config):
        super().__init__(name="advanced_filler", priority=80)
        self.config = config

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """
        高级槽位填充逻辑
        """
        print(f"[AdvancedSlotFiller] Processing intent: {intent_result.intent}")
        
        # 这里可以实现高级逻辑
        # 例如：
        # 1. 调用大模型进行语义理解
        # 2. 调用知识图谱进行实体链接
        # 3. 使用NER模型提取实体
        
        if intent_result.slots is None:
            intent_result.slots = {}
        
        intent_result.slots["processed_by"] = self.name
        intent_result.metadata["advanced_processing"] = True
        
        return intent_result


def example_usage():
    """
    使用示例
    """
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    
    # 创建自定义槽位提取器实例
    custom_filler = CustomSlotFiller(
        config=None,  # 这里可以传入配置
        custom_param="my_special_config"
    )
    advanced_filler = AdvancedSlotFiller(config=None)
    
    # 初始化 RuleEngine，注册自定义槽位提取器
    engine = RuleEngine(
        config_dir=config_dir,
        extra_slot_fillers=[custom_filler, advanced_filler]
    )
    
    print("=" * 60)
    print("示例 1: 使用默认槽位提取器")
    print("=" * 60)
    text1 = "我想预订明天去北京的机票"
    result1 = engine.process(text1)
    print(f"文本: {text1}")
    print(f"意图: {result1.intent}")
    print(f"槽位: {result1.slots}")
    print()
    
    print("=" * 60)
    print("示例 2: 通过 context 指定使用 custom_filler")
    print("=" * 60)
    text2 = "我想预订明天去北京的机票"
    context2 = {"slot_filler": "custom_filler"}
    result2 = engine.process(text2, context=context2)
    print(f"文本: {text2}")
    print(f"Context: {context2}")
    print(f"意图: {result2.intent}")
    print(f"槽位: {result2.slots}")
    print()
    
    print("=" * 60)
    print("示例 3: 通过 context 指定使用 advanced_filler")
    print("=" * 60)
    text3 = "查询天气"
    context3 = {"slot_filler": "advanced_filler"}
    result3 = engine.process(text3, context=context3)
    print(f"文本: {text3}")
    print(f"Context: {context3}")
    print(f"意图: {result3.intent}")
    print(f"槽位: {result3.slots}")
    print(f"元数据: {result3.metadata}")
    print()
    
    print("=" * 60)
    print("示例 4: 指定不存在的槽位提取器，自动降级到默认")
    print("=" * 60)
    text4 = "帮我查询订单"
    context4 = {"slot_filler": "non_existent_filler"}
    result4 = engine.process(text4, context=context4)
    print(f"文本: {text4}")
    print(f"Context: {context4}")
    print(f"意图: {result4.intent}")
    print(f"槽位: {result4.slots}")
    print()


if __name__ == "__main__":
    example_usage()
