#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 XwCustomSlotFiller 的实现 - 新的列表格式
"""
from datetime import datetime
from pandas import Timestamp
from intent_recognition.core.rule_engine import IntentResult
from intent_recognition.core.slot_filler import XwCustomSlotFiller
from pathlib import Path
import json


class MockConfig:
    """模拟配置对象"""
    def __init__(self):
        self.regex_patterns = {"slots": {}}
    
    def get_intent_slots(self, intent_name: str):
        return []


def create_test_data():
    """创建测试数据（与用户提供的数据格式相同）"""
    return [
        {
            '20251124-0-18-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-24 21:20:00'),
                'end_time': Timestamp('2025-11-24 22:28:40'),
                'satellites': {'CSCN-A0015': 1.0}
            }
        },
        {
            '20251124-0-19-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-24 22:38:41'),
                'end_time': Timestamp('2025-11-24 23:56:29'),
                'satellites': {'CSCN-A0015': 1.48}
            }
        },
        {
            '20251124-0-20-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-24 23:59:44'),
                'end_time': Timestamp('2025-11-25 00:55:14'),
                'satellites': None
            }
        },
        {
            '20251124-0-21-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-25 00:56:36'),
                'end_time': Timestamp('2025-11-25 02:02:50'),
                'satellites': {'CSCN-A0015': 1.45}
            }
        },
        {
            '20251125-0-35-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-25 09:00:00'),
                'end_time': Timestamp('2025-11-25 14:07:32'),
                'satellites': {
                    'CSCN-A0010': 0.45,
                    'CSCN-A0015': 3.2,
                    'CSCN-A0014': 3.05
                }
            }
        },
        {
            '20251125-0-36-20-2-CSCN-A0007-CSCN-A0026': {
                'start_time': Timestamp('2025-11-25 19:44:26'),
                'end_time': Timestamp('2025-11-25 23:53:45'),
                'satellites': {'CSCN-A0015': 2.2}
            }
        },
    ]


def test_xw_slot_filler():
    """测试 XwCustomSlotFiller"""
    config = MockConfig()
    filler = XwCustomSlotFiller(config)
    
    # 创建测试数据
    data_list = create_test_data()
    
    # 创建意图识别结果
    intent_result = IntentResult(
        intent="test_intent",
        confidence=0.9,
        recognizer="test_recognizer",
        slots={},
        raw_matches={},
        metadata={"data": data_list}
    )
    
    # 执行槽位填充
    result = filler.fill_slots(intent_result, "test_text")
    
    # 输出结果
    print("\n" + "="*80)
    print("测试结果 - 新的列表格式")
    print("="*80)
    print(f"\nIntent: {result.intent}")
    print(f"Confidence: {result.confidence}")
    print(f"Recognizer: {result.recognizer}")
    print(f"\nSlots (anomalies):")
    
    if 'anomalies' in result.slots:
        anomalies = result.slots['anomalies']
        for category, info_list in anomalies.items():
            if info_list:  # 只显示非空列表
                print(f"\n  {category}:")
                print(f"    共 {len(info_list)} 条异常")
                for idx, info in enumerate(info_list, 1):
                    print(f"    [{idx}]")
                    for key, value in info.items():
                        print(f"      {key}: {value}")
    
    print("\n" + "="*80)
    print("详细 JSON 输出:")
    print("="*80)
    # 转换为可序列化的格式
    output_dict = {
        "intent": result.intent,
        "confidence": result.confidence,
        "recognizer": result.recognizer,
        "anomalies": result.slots.get('anomalies', {})
    }
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_xw_slot_filler()
