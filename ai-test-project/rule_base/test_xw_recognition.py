#!/usr/bin/env python3
"""
意图识别框架测试示例
"""
from intent_recognition.core.rule_engine import RuleEngine
from intent_recognition.core.xw_matcher import XwCustomMatcher

def test_basic():
    print("=" * 60)
    print("测试自定义识别器基本功能")
    print("=" * 60)
    from pathlib import Path
    from intent_recognition.core.rule_engine import ConfigManager
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    config = ConfigManager(config_dir)
    excel_recognizer = XwCustomMatcher(config=config, priority=200)
    
    engine = RuleEngine(
        config_dir=config_dir,
        extra_recognizers=[excel_recognizer]
    )
    
    test_cases = [
        "我想预订从北京到上海的机票",
        "12月25日从深圳飞广州",
        "查询订单ABC12345678",
        "取消订单XYZ98765432",
        "帮我查看我的订单状态",
        "随便说点什么",
    ]
    
    for text in test_cases:
        result = engine.process(text)
        print(f"\n输入: {text}")
        print(f"意图: {result.intent} (置信度: {result.confidence:.2f}, 识别器: {result.recognizer})")
        print(f"槽位: {result.slots}")
        if result.metadata:
            print(f"元数据: {result.metadata}")


def test_xw_advance():
    print("=" * 60)
    print("测试自定义识别器excel功能")
    print("=" * 60)
    from pathlib import Path
    from intent_recognition.core.rule_engine import ConfigManager
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    config = ConfigManager(config_dir)
    excel_recognizer = XwCustomMatcher(config=config, priority=200)
    
    engine = RuleEngine(
        config_dir=config_dir,
        extra_recognizers=[excel_recognizer]
    )
    
    print(f"✅ 使用真实配置目录: {config_dir}")
    print(f"   - 配置文件: xw_excel.json (自动加载)")
    print(f"   - default_excel_type: {config.excel_analyzer.get('default_excel_type')}")
    print(f"   - segment_pattern: {config.excel_analyzer.get('segment_pattern')}")
    print(f"   - duration_threshold: {config.excel_analyzer.get('duration_threshold')}s")
    print()
    
    test_cases = [
        {
            "name": "测试1: 旧格式 (merged) - 多个 sheet，行合并",
            "text": "",  # text 参数未使用
            "context": {
                'trigger_excel': True,  # 必须设置为 True 才会触发 Excel 解析
                'excel_type': 'merged'
            }
        },
        {
            "name": "测试2: 新格式 (standardized) - 单个 sheet，无行合并",
            "text": "",
            "context": {
                'trigger_excel': True,
                'excel_type': 'standardized'
            }
        },
        {
            "name": "测试3: 动态配置 - 指定不同的 Excel 文件",
            "text": "",
            "context": {
                'trigger_excel': True,
                'excel_type': 'standardized',
                # 可以动态指定不同的文件和参数
                'execl_path': 'execl/StatisticsOnDisconnectedService_standardized_20251209_152318.xlsx',
                'sheet_name': 'Sheet1',
                'duration_threshold': 20.0,  # 不同的阈值\
                'ignore_no_interruption': False
            }
        },
        {
            "name": "测试4: 未触发 - 不应该执行 Excel 解析",
            "text": "12月25日从深圳飞广州",
        },
    ]
    for i, test_case in enumerate(test_cases, 1):
        print("=" * 80)
        print(test_case["name"])
        print("=" * 80)
        # 使用 RuleEngine 处理
        result = engine.process(
            text=test_case["text"],
            context=test_case.get("context", {})
        )
        if result and result.intent == "excel_interruption_analysis":
            print(f"\n✅ 解析结果:")
            print(f"   - 意图: {result.intent}")
            print(f"   - 识别器: {result.recognizer}")
            print(f"   - 置信度: {result.confidence:.2f}")
            print(f"   - excel_type: {result.metadata.get('excel_type')}")
            print(f"   - sheet_name: {result.metadata.get('sheet_name')}")
            print(f"   - duration_threshold: {result.metadata.get('duration_threshold')}s")
            print(f"   - result_count: {result.metadata.get('result_count')} 条")
            print(f"\n   前2条数据:")
            data = result.metadata.get('data', [])
            for j, item in enumerate(data[:2], 1):
                for segment_name, satellites in item.items():
                    print(f"   {j}. {segment_name}: {len(satellites) if satellites else 0} 个卫星")
        else:
            print(f"\nℹ️ 未识别到 Excel 意图 (这是预期行为 - 没有 trigger_excel 或其他识别器处理)")
            if result:
                print(f"   - 识别到的意图: {result.intent}")
                print(f"   - 识别器: {result.recognizer}")
        
        print()
    
    
        
    
    
if __name__ == "__main__":
    test_basic()  # 测试基本功能

    test_xw_advance()  # 测试自定义 Excel 识别器高级功能
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
