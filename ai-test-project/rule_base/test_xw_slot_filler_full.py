#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试 XwCustomSlotFiller 的实现 - 新的列表格式
使用用户提供的完整数据
"""
from pandas import Timestamp
from intent_recognition.core.rule_engine import IntentResult
from intent_recognition.core.slot_filler import XwCustomSlotFiller
import json


class MockConfig:
    """模拟配置对象"""
    def __init__(self):
        self.regex_patterns = {"slots": {}}
    
    def get_intent_slots(self, intent_name: str):
        return []


def create_full_test_data():
    """创建完整测试数据 - 用户提供的所有数据"""
    return [
        {'20251124-0-18-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-24 21:20:00'), 'end_time': Timestamp('2025-11-24 22:28:40'), 'satellites': {'CSCN-A0015': 1.0}}},
        {'20251124-0-19-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-24 22:38:41'), 'end_time': Timestamp('2025-11-24 23:56:29'), 'satellites': {'CSCN-A0015': 1.48}}},
        {'20251124-0-20-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-24 23:59:44'), 'end_time': Timestamp('2025-11-25 00:55:14'), 'satellites': None}},
        {'20251124-0-21-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 00:56:36'), 'end_time': Timestamp('2025-11-25 02:02:50'), 'satellites': {'CSCN-A0015': 1.45}}},
        {'20251124-0-23-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 02:12:52'), 'end_time': Timestamp('2025-11-25 02:24:30'), 'satellites': None}},
        {'20251124-0-24-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 02:35:20'), 'end_time': Timestamp('2025-11-25 02:45:51'), 'satellites': None}},
        {'20251124-0-25-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 02:46:48'), 'end_time': Timestamp('2025-11-25 02:56:24'), 'satellites': None}},
        {'20251124-0-26-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 06:35:02'), 'end_time': Timestamp('2025-11-25 06:42:59'), 'satellites': None}},
        {'20251124-0-27-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 06:45:32'), 'end_time': Timestamp('2025-11-25 06:54:37'), 'satellites': None}},
        {'20251124-0-28-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 06:56:01'), 'end_time': Timestamp('2025-11-25 07:06:01'), 'satellites': None}},
        {'20251124-0-22-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 07:06:52'), 'end_time': Timestamp('2025-11-25 09:00:00'), 'satellites': {'CSCN-A0021': 0.45, 'CSCN-A0020': 0.4, 'CSCN-A0012': 1.4, 'CSCN-A0011': 0.45, 'CSCN-A0010': 0.45}}},
        {'20251125-0-35-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 09:00:00'), 'end_time': Timestamp('2025-11-25 14:07:32'), 'satellites': {'CSCN-A0010': 0.45, 'CSCN-A0015': 3.2, 'CSCN-A0014': 3.05}}},
        {'20251125-0-40-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 14:07:43'), 'end_time': Timestamp('2025-11-25 14:17:56'), 'satellites': None}},
        {'20251125-0-41-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 14:18:56'), 'end_time': Timestamp('2025-11-25 14:28:14'), 'satellites': None}},
        {'20251125-0-42-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 14:30:18'), 'end_time': Timestamp('2025-11-25 14:38:26'), 'satellites': None}},
        {'20251125-0-43-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 14:41:48'), 'end_time': Timestamp('2025-11-25 14:48:24'), 'satellites': None}},
        {'20251125-0-44-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 19:03:09'), 'end_time': Timestamp('2025-11-25 19:10:36'), 'satellites': None}},
        {'20251125-0-45-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 19:13:10'), 'end_time': Timestamp('2025-11-25 19:21:50'), 'satellites': None}},
        {'20251125-0-46-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 19:23:35'), 'end_time': Timestamp('2025-11-25 19:33:17'), 'satellites': None}},
        {'20251125-0-47-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 19:33:56'), 'end_time': Timestamp('2025-11-25 19:44:23'), 'satellites': None}},
        {'20251125-0-36-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 19:44:26'), 'end_time': Timestamp('2025-11-25 23:53:45'), 'satellites': {'CSCN-A0015': 2.2}}},
        {'20251125-0-37-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-25 23:55:49'), 'end_time': Timestamp('2025-11-26 00:47:19'), 'satellites': None}},
        {'20251125-0-38-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 00:52:35'), 'end_time': Timestamp('2025-11-26 02:20:27'), 'satellites': {'CSCN-A0010': 1.05, 'CSCN-A0020': 1.01, 'CSCN-A0009': 1.01, 'CSCN-A0008': 1.02, 'CSCN-A0007': 1.04, 'CSCN-A0016': 1.05, 'CSCN-A0015': 2.3, 'CSCN-A0014': 1.03, 'CSCN-A0013': 1.01, 'CSCN-A0017': 1.06, 'CSCN-A0018': 1.02, 'CSCN-A0019': 1.04, 'CSCN-A0021': 1.05, 'CSCN-A0022': 1.04, 'CSCN-A0023': 1.06, 'CSCN-A0024': 1.04, 'CSCN-A0025': 1.05, 'CSCN-A0026': 1.02, 'CSCN-A0011': 1.19, 'CSCN-A0012': 1.04}}},
        {'20251125-0-48-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 06:20:39'), 'end_time': Timestamp('2025-11-26 06:27:14'), 'satellites': None}},
        {'20251125-0-49-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 06:30:54'), 'end_time': Timestamp('2025-11-26 06:38:58'), 'satellites': None}},
        {'20251125-0-50-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 06:41:34'), 'end_time': Timestamp('2025-11-26 06:50:49'), 'satellites': {'CSCN-A0015': 0.42}}},
        {'20251125-0-51-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 06:52:07'), 'end_time': Timestamp('2025-11-26 07:02:15'), 'satellites': None}},
        {'20251125-0-39-20-2-CSCN-A0007-CSCN-A0026': {'start_time': Timestamp('2025-11-26 07:02:49'), 'end_time': Timestamp('2025-11-26 09:40:30.947000'), 'satellites': {'CSCN-A0015': 1.35}}}
    ]


def test_xw_slot_filler_full():
    """使用完整数据测试 XwCustomSlotFiller"""
    config = MockConfig()
    filler = XwCustomSlotFiller(config)
    
    # 创建完整测试数据
    data_list = create_full_test_data()
    
    # 创建意图识别结果
    intent_result = IntentResult(
        intent="xw_anomaly_recognition",
        confidence=0.95,
        recognizer="xw_matcher",
        slots={},
        raw_matches={},
        metadata={"data": data_list}
    )
    
    # 执行槽位填充
    result = filler.fill_slots(intent_result, "test_text")
    
    # 输出结果
    print("\n" + "="*80)
    print("完整数据测试结果 - 新的列表格式")
    print("="*80)
    print(f"\nIntent: {result.intent}")
    print(f"Confidence: {result.confidence}")
    print(f"Recognizer: {result.recognizer}")
        
    anomalies = result.slots.get('anomalies', {})
    total_anomalies = sum(len(info_list) for info_list in anomalies.values())
    print(f"\n总例常数量: {total_anomalies}")
        
    for category, info_list in anomalies.items():
        if info_list:
            print(f"\n{category}:")
            print(f"  共 {len(info_list)} 条异常")
            for idx, info in enumerate(info_list, 1):
                print(f"  [{idx}] ", end="")
                # 仅显示一些关键信息
                if 'satellite' in info:
                    print(f"{info['satellite']} | {info['start_time']} ~ {info['end_time']}", end="")
                    if 'pass_count' in info:
                        print(f" | {info['pass_count']}圈次", end="")
                elif 'satellites' in info:
                    sat_str = ','.join(info['satellites'][:3])  # 只显示前3个
                    if len(info['satellites']) > 3:
                        sat_str += f"... (共{len(info['satellites'])}颗)"
                    print(f"{sat_str} | {info['start_time']} ~ {info['end_time']}", end="")
                print()
        
    print("\n" + "="*80)
    
    print("详细 JSON 输出:")
    print("="*80)
    import json
    output_dict = {
        "intent": result.intent,
        "confidence": result.confidence,
        "recognizer": result.recognizer,
        "total_anomalies": total_anomalies,
        "anomalies": result.slots.get('anomalies', {})
    }
    print(json.dumps(output_dict, indent=2, ensure_ascii=False, default=str))
    print()


if __name__ == "__main__":
    test_xw_slot_filler_full()