# XwCustomSlotFiller 完整使用指南

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

### 输入格式

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

### 输出格式（重要变更）

处理后的结果存储在 `intent_result.slots['anomalies']` 中，**新版本采用列表聚合格式**：

```python
Dict[str, List[Dict[str, Any]]]
```

其中键是异常类别（字符串），值是异常列表。**同类型的多个异常会被聚合到同一个列表中**：

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

## 使用示例

### 基础使用

```python
from intent_recognition.core.rule_engine import IntentResult
from intent_recognition.core.slot_filler import XwCustomSlotFiller
from pandas import Timestamp

# 创建配置对象和填充器
config = ...
filler = XwCustomSlotFiller(config)

# 创建意图结果
intent_result = IntentResult(
    intent="xw_anomaly",
    confidence=0.95,
    recognizer="xw_matcher",
    metadata={
        "data": [
            # 你的卫星数据...
        ]
    }
)

# 执行槽位填充
result = filler.fill_slots(intent_result, "text")

# 访问结果
anomalies = result.slots['anomalies']
```

### 访问特定类型的异常

```python
# 定义异常类别常量
MULTI_PASS_KEY = "单颗星异常-多圈次长时间（涉及多个落地星）不通"
SINGLE_PASS_KEY = "单颗星异常-单圈次（单落地星）全程或短时间不通"
MULTI_SAT_KEY = "多颗星异常-多颗卫星联合异常"

# 获取特定类型的异常
multi_pass_anomalies = result.slots['anomalies'].get(MULTI_PASS_KEY, [])
single_pass_anomalies = result.slots['anomalies'].get(SINGLE_PASS_KEY, [])
multi_sat_anomalies = result.slots['anomalies'].get(MULTI_SAT_KEY, [])

# 遍历异常
for anomaly in single_pass_anomalies:
    print(f"卫星: {anomaly['satellite']}")
    print(f"时间: {anomaly['start_time']} ~ {anomaly['end_time']}")

# 统计异常数量
total_count = sum(len(v) for v in result.slots['anomalies'].values())
print(f"总异常数: {total_count}")
```

### 与 RuleEngine 集成

```python
from intent_recognition.core.rule_engine import RuleEngine

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

# 访问异常信息
anomalies = result.slots['anomalies']
```

## 关键改进

### 新版本相比旧版本的改进

1. **列表聚合**：同一类型的多个异常被聚合到一个列表中，而不是使用数字后缀
   - 旧格式：`"异常类型#1": {...}, "异常类型#2": {...}`
   - 新格式：`"异常类型": [{...}, {...}]`

2. **更清晰的数据结构**
   - 便于遍历同类型的所有异常
   - 容易获取统计信息（如某类型异常的数量）
   - JSON 序列化更自然

3. **更好的扩展性**
   - 新增异常时无需修改键名
   - 支持动态生成异常报告

## 性能考虑

- **时间复杂度**：O(n)，其中 n 是数据列表长度
- **空间复杂度**：O(m)，其中 m 是异常总数
- **大数据集处理**：对于包含数千条记录的数据集仍能快速处理

## 常见问题

### Q: 为什么同一卫星的多个单圈次异常不会合并？
A: 按照业务规则，只有连续的同一颗卫星数据才会被分组为多圈次异常。被无卫星数据分隔的异常会被视为单独事件。

### Q: 如何判断异常列表是否为空？
A: 检查列表长度：
```python
if result.slots['anomalies'].get(MULTI_PASS_KEY, []):
    print("存在多圈次异常")
```

### Q: 可以从结果中提取所有卫星名称吗？
A: 可以，通过遍历异常列表：
```python
all_satellites = set()
for anomaly_list in result.slots['anomalies'].values():
    for anomaly in anomaly_list:
        if 'satellite' in anomaly:
            all_satellites.add(anomaly['satellite'])
        elif 'satellites' in anomaly:
            all_satellites.update(anomaly['satellites'])
```

### Q: 多颗星异常中的 note 字段是什么意思？
A: 这是一个占位符，表示该字段的具体参数提取将在后续版本实现。当前版本返回固定的占位符文本。

## 测试

运行测试脚本验证实现：

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base

# 简单测试
python test_xw_slot_filler.py

# 完整数据测试
python test_xw_slot_filler_full.py
```

## 后期扩展计划

- 多颗星异常的详细参数提取（当前为占位符）
- 更复杂的异常分类规则
- 异常时间段的合并或分割逻辑
- 大数据集处理的性能优化
