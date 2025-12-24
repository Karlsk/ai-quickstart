#!/usr/bin/env python3
"""
测试自定义槽位提取器功能
"""
from typing import Any, Dict
from intent_recognition import IntentEngine, BaseSlotFiller


class CustomSlotFiller(BaseSlotFiller):
    """自定义槽位提取器：演示如何添加自定义逻辑"""

    def __init__(self, config=None):
        super().__init__(name="custom_filler", priority=90)
        self.config = config

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """添加自定义槽位"""
        print(f"[CustomSlotFiller] 处理文本: {original_text}")
        
        if intent_result.slots is None:
            intent_result.slots = {}
        
        # 添加自定义标记
        intent_result.slots["processed_by"] = self.name
        intent_result.slots["text_length"] = len(original_text)
        
        return intent_result


class LLMSlotFiller(BaseSlotFiller):
    """模拟大模型槽位提取器"""

    def __init__(self, config=None):
        super().__init__(name="llm_filler", priority=80)
        self.config = config

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """模拟大模型进行槽位提取"""
        print(f"[LLMSlotFiller] 使用大模型处理: {original_text}")
        
        if intent_result.slots is None:
            intent_result.slots = {}
        
        # 添加模拟的大模型处理结果
        intent_result.slots["processed_by"] = self.name
        intent_result.slots["llm_enhanced"] = True
        intent_result.metadata["llm_used"] = True
        
        return intent_result


def test_default_slot_filler():
    """测试默认槽位提取器"""
    print("=" * 60)
    print("测试 1: 使用默认槽位提取器")
    print("=" * 60)
    
    engine = IntentEngine()
    text = "我想预订从北京到上海的机票"
    result = engine.handle(text)
    
    print(f"文本: {text}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")
    print()


def test_custom_slot_filler():
    """测试通过 context 指定自定义槽位提取器"""
    print("=" * 60)
    print("测试 2: 通过 context 指定 custom_filler")
    print("=" * 60)
    
    # 注册自定义槽位提取器
    custom_filler = CustomSlotFiller()
    engine = IntentEngine(extra_slot_fillers=[custom_filler])
    
    text = "查询订单ABC12345678"
    context = {"slot_filler": "custom_filler"}
    result = engine.handle(text, context)
    
    print(f"文本: {text}")
    print(f"Context: {context}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")
    print()


def test_llm_slot_filler():
    """测试大模型槽位提取器"""
    print("=" * 60)
    print("测试 3: 使用大模型槽位提取器")
    print("=" * 60)
    
    llm_filler = LLMSlotFiller()
    engine = IntentEngine(extra_slot_fillers=[llm_filler])
    
    text = "帮我查询天气"
    context = {"slot_filler": "llm_filler"}
    result = engine.handle(text, context)
    
    print(f"文本: {text}")
    print(f"Context: {context}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")
    print(f"元数据: {result.metadata}")
    print()


def test_multiple_slot_fillers():
    """测试注册多个槽位提取器"""
    print("=" * 60)
    print("测试 4: 注册多个槽位提取器并动态切换")
    print("=" * 60)
    
    custom_filler = CustomSlotFiller()
    llm_filler = LLMSlotFiller()
    engine = IntentEngine(extra_slot_fillers=[custom_filler, llm_filler])
    
    test_cases = [
        ("预订机票", None),  # 使用默认
        ("查询订单", {"slot_filler": "custom_filler"}),  # 使用自定义
        ("查询天气", {"slot_filler": "llm_filler"}),  # 使用大模型
    ]
    
    for text, context in test_cases:
        result = engine.handle(text, context)
        filler_name = context.get("slot_filler", "default") if context else "default"
        print(f"\n文本: {text}")
        print(f"指定提取器: {filler_name}")
        print(f"意图: {result.intent}")
        print(f"槽位: {result.slots}")


def test_fallback_to_default():
    """测试不存在的槽位提取器自动降级"""
    print("\n" + "=" * 60)
    print("测试 5: 指定不存在的槽位提取器，自动降级到默认")
    print("=" * 60)
    
    engine = IntentEngine()
    text = "取消订单"
    context = {"slot_filler": "non_existent_filler"}
    result = engine.handle(text, context)
    
    print(f"文本: {text}")
    print(f"Context: {context}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")
    print("注意: 应该会在日志中看到降级警告")
    print()


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    
    test_default_slot_filler()
    test_custom_slot_filler()
    test_llm_slot_filler()
    test_multiple_slot_fillers()
    test_fallback_to_default()
    
    print("=" * 60)
    print("所有测试完成!")
    print("=" * 60)
