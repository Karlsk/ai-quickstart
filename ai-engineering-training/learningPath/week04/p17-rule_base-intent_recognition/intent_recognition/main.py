from core.rule_engine import RuleBasedIntentChain


def main():
    """
    主函数 - 系统演示和测试
    ======================

    功能说明:
    - 演示 LangChain 风格意图识别系统的完整功能
    - 提供多种测试用例验证系统性能
    - 展示单个识别和批量处理两种使用模式
    - 输出详细的识别结果和性能指标

    测试覆盖:
    1. 正则匹配测试: 结构化输入的精确识别
    2. 关键词匹配测试: 自然语言的模糊匹配
    3. 槽位提取测试: 参数信息的自动提取
    4. 未知意图测试: 兜底机制的有效性
    5. 批量处理测试: 系统的处理效率

    输出信息:
    - 识别的意图类型和置信度
    - 提取的槽位参数
    - 匹配的规则和推理过程
    - 系统性能和准确率统计
    """
    print("=== LangChain 风格的基于规则意图识别系统 (完整注释版) ===\n")

    # 创建意图识别链实例
    intent_chain = RuleBasedIntentChain()

    # 设计多样化的测试用例
    test_cases = [
        "我要查订单号123456的物流状态",  # 测试正则匹配 + 槽位提取
        "退款退款，我不要这个商品了",  # 测试正则匹配
        "帮我开个发票吧",  # 测试正则匹配
        "昨天下的订单888888想要退货",  # 测试关键词匹配 + 复杂槽位提取
        "查一下我的快递到了吗",  # 测试关键词匹配
        "不知道说什么",  # 测试未知意图兜底机制
        "我想开个1000元的发票"  # 测试槽位提取(金额)
    ]

    print("LangChain 风格意图识别测试:")
    print("=" * 80)

    # 逐个测试用例进行详细分析
    for i, text in enumerate(test_cases, 1):
        # 执行意图识别
        result = intent_chain.invoke({"text": text})

        # 输出详细的识别结果
        print(f"测试 {i}: {text}")
        print(f"  意图: {result['intent']}")  # 识别的意图类型
        print(f"  置信度: {result['confidence']:.2f}")  # 置信度分数
        print(f"  槽位: {result['slots']}")  # 提取的槽位参数
        print(f"  匹配规则: {result['matched_rules']}")  # 匹配的规则标识
        print(f"  推理过程: {result['reasoning']}")  # 推理过程说明

        # 如果有提取的实体，额外显示
        if result['extracted_entities']:
            print(f"  提取实体: {result['extracted_entities']}")
        print("-" * 80)

    # 演示批量处理能力
    print("\n批量处理演示:")
    print("=" * 80)

    # 批量处理的测试数据
    batch_texts = [
        "查订单123",  # 简短的订单查询
        "退货申请",  # 简短的退货申请
        "开发票"  # 简短的开票申请
    ]

    # 批量执行意图识别
    batch_results = [intent_chain.invoke({"text": text}) for text in batch_texts]

    # 输出批量处理结果的摘要
    for text, result in zip(batch_texts, batch_results):
        print(f"{text} -> {result['intent']} (置信度: {result['confidence']:.2f})")

    print("\n" + "=" * 80)
    print("系统特性总结:")
    print("1. 多策略融合: 正则匹配 + 关键词匹配")
    print("2. 智能决策: 基于置信度和规则优先级")
    print("3. 槽位提取: 自动提取业务参数")
    print("4. 可解释性: 提供详细的推理过程")
    print("5. 兜底机制: 未知输入的优雅处理")
    print("6. 模块化设计: LangChain 风格的组件架构")


if __name__ == "__main__":
    main()
