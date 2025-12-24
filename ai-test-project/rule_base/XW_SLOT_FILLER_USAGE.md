# XwCustomSlotFiller 使用指南

## 概述

`XwCustomSlotFiller` 是一个遥感异常分析槽位填充器，用于从卫星数据中提取和分类异常信息。

## 核心分类规则

### 1. 单颗星异常 (Single Satellite Anomaly)

#### 多圈次长时间异常
- **条件**：当前数据和下一条数据都是同一颗卫星
- **参数提取**：
  - `satellite`: 卫星名称
  - `start_time`: 第一条数据的开始时间
  - `end_time`: 最后一条数据的结束时间
  - `pass_count`: 涉及的圈次数量

#### 单圈次异常
- **条件**：单条数据或前一条数据不是同一颗卫星
- **参数提取**：
  - `satellite`: 卫星名称
  - `start_time`: 本条数据的开始时间
  - `end_time`: 本条数据的结束时间

### 2. 多颗星异常 (Multi-Satellite Anomaly)

- **条件**：一条数据中有多颗卫星
- **参数提取**：
  - `satellites`: 卫星名称列表
  - `start_time`: 数据的开始时间
  - `end_time`: 数据的结束时间
  - `note`: 占位符，后期扩展实现

### 3. 无卫星数据 (No Satellite)

- 当 `satellites` 为 `None` 时，该条记录被跳过

## 数据格式

输入数据应该放在 `intent_result.metadata['data']` 中，格式如下：

```python
[
    {
        'record_key': {
            'start_time': Timestamp('2025-11-24 21:20:00'),
            'end_time': Timestamp('2025-11-24 22:28:40'),
            'satellites': {'CSCN-A0015': 1.0}
        }
    },
    # ... 更多记录
]
```

## 输出格式

处理后的结果存储在 `intent_result.slots['anomalies']` 中，格式为：

```
Dict[str, List[Dict[str, Any]]]
```

其中键是异常类别（字符串），值是异常列表。每个异常类别只有一个对应的列表，同类型的多个异常会被聚合到同一个列表中：

```python
{
    "单颗星异常-多圈次长时间（涉及多个落地星）不通": [
        {
            "satellite": "CSCN-A0015",
            "start_time": "2025-11-24 21:20:00",
            "end_time": "2025-11-24 23:56:29",
            "pass_count": 2
        }
    ],
    "单颗星异常-单圈次（单落地星）全程或短时间不通": [
        {
            "satellite": "CSCN-A0015",
            "start_time": "2025-11-25 00:56:36",
            "end_time": "2025-11-25 02:02:50"
        },
        {
            "satellite": "CSCN-A0015",
            "start_time": "2025-11-25 19:44:26",
            "end_time": "2025-11-25 23:53:45"
        }
    ],
    "多颗星异常-多颗卫星联合异常": [
        {
            "satellites": ["CSCN-A0021", "CSCN-A0020", ...],
            "start_time": "2025-11-25 07:06:52",
            "end_time": "2025-11-25 09:00:00",
            "note": "多颗星异常分类参数提取后期再扩展实现"
        }
    ]
}
```

### 数据格式说明

**多圈次长时间异常**：
- `satellite`: 卫星名称
- `start_time`: 第一条数据的开始时间
- `end_time`: 最后一条数据的结束时间  
- `pass_count`: 涉及的圈次数量

**单圈次异常**：
- `satellite`: 卫星名称
- `start_time`: 本条数据的开始时间
- `end_time`: 本条数据的结束时间

**多颗星异常**：
- `satellites`: 卫星名称列表
- `start_time`: 数据的开始时间
- `end_time`: 数据的结束时间
- `note`: 占位符（后期扩展）

## 使用示例

### 基础使用

```python
from intent_recognition.core.rule_engine import IntentResult, RuleEngine
from intent_recognition.core.slot_filler import XwCustomSlotFiller
from pandas import Timestamp

# 创建配置对象
config = ...  # 从 RuleEngine 获取

# 创建槽位填充器
filler = XwCustomSlotFiller(config)

# 创建意图结果
intent_result = IntentResult(
    intent="xw_anomaly",
    confidence=0.95,
    recognizer="xw_matcher",
    metadata={
        "data": [
            {
                'record_key': {
                    'start_time': Timestamp('2025-11-24 21:20:00'),
                    'end_time': Timestamp('2025-11-24 22:28:40'),
                    'satellites': {'CSCN-A0015': 1.0}
                }
            },
            # ... 更多数据
        ]
    }
)

# 执行槽位填充
result = filler.fill_slots(intent_result, "text")

# 访问结果
anomalies = result.slots['anomalies']
for category, info in anomalies.items():
    print(f"{category}: {info}")
```

### 与 RuleEngine 集成

```python
from intent_recognition import IntentEngine

# 创建引擎（会自动包含 SlotFiller）
engine = IntentEngine()

# 处理文本
result = engine.handle("your_text")

# 访问异常信息
if 'anomalies' in result.slots:
    anomalies = result.slots['anomalies']
    # 处理异常信息
```

### 自定义集成

如果需要为 RuleEngine 添加 XwCustomSlotFiller：

```python
from intent_recognition.core.rule_engine import RuleEngine
from intent_recognition.core.slot_filler import XwCustomSlotFiller

config = ...
xw_filler = XwCustomSlotFiller(config)

engine = RuleEngine(
    config_dir="path/to/config",
    extra_slot_fillers=[xw_filler]
)

# 使用指定的槽位填充器
result = engine.process(
    "text",
    context={"slot_filler": "xw_slot_filler"}
)
```

## 实现细节

### 多圈次异常的连续性检查

`_find_same_satellite_end` 方法会持续扫描数据列表，直到遇到：
- 没有卫星数据（`satellites` 为 `None`）
- 多颗卫星
- 不同的单颗卫星

### 命名约定

为了支持多个相同类型的异常，异常类别键使用 `#数字` 后缀进行区分：
- `单颗星异常-多圈次长时间（涉及多个落地星）不通#1`
- `单颗星异常-单圈次（单落地星）全程或短时间不通#1`
- `多颗星异常-多颗卫星联合异常#1`

## 测试

运行测试脚本验证实现：

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base
python test_xw_slot_filler.py          # 简单测试
python test_xw_slot_filler_full.py     # 完整数据测试
```

## 后期扩展

- 多颗星异常的详细参数提取（当前为占位符）
- 更复杂的异常分类规则
- 异常时间段的合并或分割逻辑
- 性能优化（对大数据集的处理）
