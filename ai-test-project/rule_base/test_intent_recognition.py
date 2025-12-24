#!/usr/bin/env python3
"""
意图识别框架测试示例
"""
from intent_recognition import IntentEngine


def test_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("基础使用示例")
    print("=" * 60)
    
    engine = IntentEngine()
    
    test_cases = [
        "我想预订从北京到上海的机票",
        "12月25日从深圳飞广州",
        "查询订单ABC12345678",
        "取消订单XYZ98765432",
        "帮我查看我的订单状态",
        "随便说点什么",
    ]
    
    for text in test_cases:
        result = engine.handle(text)
        print(f"\n输入: {text}")
        print(f"意图: {result.intent} (置信度: {result.confidence:.2f}, 识别器: {result.recognizer})")
        print(f"槽位: {result.slots}")
        if result.metadata:
            print(f"元数据: {result.metadata}")


def test_context_aware():
    """上下文感知示例（FSM）"""
    print("\n" + "=" * 60)
    print("上下文感知示例")
    print("=" * 60)
    
    engine = IntentEngine()
    context = {}
    
    # 第一轮
    text1 = "查询订单ABC12345678"
    result1 = engine.handle(text1, context)
    context["last_intent"] = result1.intent
    print(f"\n第一轮输入: {text1}")
    print(f"识别结果: {result1.intent} (via {result1.recognizer})")
    
    # 第二轮 - 模糊输入，可能使用FSM延续上下文
    text2 = "这个怎么样了"
    result2 = engine.handle(text2, context)
    print(f"\n第二轮输入: {text2}")
    print(f"识别结果: {result2.intent} (via {result2.recognizer})")
    print(f"元数据: {result2.metadata}")


def test_slot_filling():
    """槽位填充示例"""
    print("\n" + "=" * 60)
    print("槽位填充示例")
    print("=" * 60)
    
    engine = IntentEngine()
    
    # 正则直接提取槽位
    text = "预订2024-12-25从北京到上海的机票"
    result = engine.handle(text)
    print(f"\n输入: {text}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")
    print(f"  - 出发城市: {result.slots.get('departure_city')}")
    print(f"  - 到达城市: {result.slots.get('arrival_city')}")
    print(f"  - 出发日期: {result.slots.get('departure_date')}")


def test_recognizer_priority():
    """识别器优先级示例"""
    print("\n" + "=" * 60)
    print("识别器优先级示例")
    print("=" * 60)
    
    engine = IntentEngine()
    
    # 这条输入会同时命中正则和关键词，但正则优先级更高
    text = "我要订从杭州到成都的机票"
    result = engine.handle(text)
    print(f"\n输入: {text}")
    print(f"意图: {result.intent}")
    print(f"识别器: {result.recognizer} (正则优先级 > 关键词)")
    print(f"槽位: {result.slots}")


def test_timeout_and_degradation():
    """超时降级示例（演示框架支持）"""
    print("\n" + "=" * 60)
    print("超时降级机制")
    print("=" * 60)
    
    # 创建一个超时很短的引擎
    engine = IntentEngine(timeout_per_recognizer=0.001)  # 极短超时
    
    text = "从北京到上海的机票"
    result = engine.handle(text)
    print(f"\n输入: {text}")
    print(f"结果: {result.intent}")
    print("注意: 如果某个识别器超时，会在日志中看到降级信息，但不影响其他识别器")


if __name__ == "__main__":
    test_basic_usage()
    test_context_aware()
    test_slot_filling()
    test_recognizer_priority()
    test_timeout_and_degradation()
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
