# 多槽位提取器支持说明

## 概述

现在 RuleEngine 支持配置多个槽位提取器（Slot Filler），类似于 matcher 的设计模式。你可以：

1. **注册多个槽位提取器**：在初始化 RuleEngine 时通过 `extra_slot_fillers` 参数注册
2. **动态选择提取器**：通过 context 参数中的 `slot_filler` 字段指定使用哪个提取器
3. **自动降级**：如果指定的提取器不存在，自动降级到默认提取器（SlotFiller）

## 核心改动

### 1. 新增基类 `BaseSlotFiller`

```python
class BaseSlotFiller:
    """槽位提取器基类"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
    
    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """填充槽位 - 子类必须实现"""
        raise NotImplementedError
```

### 2. SlotFiller 继承 BaseSlotFiller

```python
class SlotFiller(BaseSlotFiller):
    """默认槽位填充器"""
    
    def __init__(self, config, llm_filler=None, llm_timeout=2.0):
        super().__init__(name="default_slot_filler", priority=100)
        # ... 原有逻辑
```

### 3. RuleEngine 支持多槽位提取器

```python
class RuleEngine:
    def __init__(
        self,
        config_dir: str | Path,
        ...,
        extra_slot_fillers: Optional[List[BaseSlotFiller]] = None,
    ):
        # 默认使用 SlotFiller，支持扩展
        slot_fillers: List[BaseSlotFiller] = [SlotFiller(self.config)]
        if extra_slot_fillers:
            slot_fillers.extend(extra_slot_fillers)
        self.slot_fillers = slot_fillers
```

### 4. 动态选择槽位提取器

```python
def process(self, text: str, context: Dict[str, Any] | None = None):
    """
    支持通过 context 指定槽位提取器：
    context = {
        "slot_filler": "custom_filler_name"
    }
    """
```

## 使用示例

### 示例 1: 创建自定义槽位提取器

```python
from intent_recognition import BaseSlotFiller

class CustomSlotFiller(BaseSlotFiller):
    """自定义槽位提取器"""
    
    def __init__(self, config=None):
        super().__init__(name="custom_filler", priority=90)
        self.config = config
    
    def fill_slots(self, intent_result, original_text: str, context=None):
        # 实现自定义槽位提取逻辑
        if intent_result.slots is None:
            intent_result.slots = {}
        
        intent_result.slots["processed_by"] = self.name
        # 添加更多自定义逻辑...
        
        return intent_result
```

### 示例 2: 注册自定义槽位提取器

```python
from intent_recognition import IntentEngine

# 创建自定义槽位提取器实例
custom_filler = CustomSlotFiller()
llm_filler = LLMSlotFiller()

# 注册到引擎
engine = IntentEngine(
    extra_slot_fillers=[custom_filler, llm_filler]
)
```

### 示例 3: 通过 context 指定槽位提取器

```python
# 使用默认槽位提取器
text = "预订机票"
result = engine.handle(text)

# 使用自定义槽位提取器
text = "查询订单"
context = {"slot_filler": "custom_filler"}
result = engine.handle(text, context)

# 使用大模型槽位提取器
text = "查询天气"
context = {"slot_filler": "llm_filler"}
result = engine.handle(text, context)
```

### 示例 4: 降级机制

```python
# 指定不存在的槽位提取器
context = {"slot_filler": "non_existent_filler"}
result = engine.handle(text, context)
# 会在日志中看到警告，并自动降级到默认提取器
```

## 典型使用场景

### 场景 1: 不同领域使用不同的槽位提取器

```python
class FlightSlotFiller(BaseSlotFiller):
    """航班领域专用槽位提取器"""
    def fill_slots(self, intent_result, original_text, context=None):
        # 航班相关的专业槽位提取逻辑
        pass

class OrderSlotFiller(BaseSlotFiller):
    """订单领域专用槽位提取器"""
    def fill_slots(self, intent_result, original_text, context=None):
        # 订单相关的专业槽位提取逻辑
        pass

# 注册
engine = IntentEngine(
    extra_slot_fillers=[FlightSlotFiller(), OrderSlotFiller()]
)

# 根据意图选择不同的提取器
if intent == "book_flight":
    context = {"slot_filler": "flight_filler"}
elif intent == "query_order":
    context = {"slot_filler": "order_filler"}
```

### 场景 2: 正则 + 大模型混合模式

```python
class RegexSlotFiller(BaseSlotFiller):
    """基于正则的槽位提取"""
    pass

class LLMSlotFiller(BaseSlotFiller):
    """基于大模型的槽位提取"""
    pass

# 先尝试正则，失败则使用大模型
result = engine.handle(text, {"slot_filler": "regex_filler"})
if not result.slots:
    result = engine.handle(text, {"slot_filler": "llm_filler"})
```

### 场景 3: A/B 测试不同的槽位提取策略

```python
import random

# 随机选择槽位提取器进行 A/B 测试
slot_filler = random.choice(["strategy_a", "strategy_b"])
context = {"slot_filler": slot_filler}
result = engine.handle(text, context)
```

## 向后兼容性

- 保留了 `engine.slot_filler` 属性，指向第一个槽位提取器（默认 SlotFiller）
- 如果不指定 `extra_slot_fillers`，行为与之前完全一致
- 如果不在 context 中指定 `slot_filler`，使用默认提取器

## 测试

运行测试：
```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base
python test_custom_slot_filler.py
```

## 文件结构

```
ai-test-project/rule_base/
├── intent_recognition/
│   ├── core/
│   │   ├── slot_filler.py          # 新增 BaseSlotFiller 基类
│   │   └── rule_engine.py          # 支持多槽位提取器
│   ├── __init__.py                 # 导出 BaseSlotFiller
│   └── main.py                     # IntentEngine 支持 extra_slot_fillers
├── test_custom_slot_filler.py      # 测试用例
└── example_custom_slot_filler.py   # 详细示例
```

## 设计优势

1. **扩展性强**：可以轻松添加新的槽位提取策略
2. **灵活性高**：运行时动态选择提取器，无需修改代码
3. **低侵入性**：符合用户偏好，对现有代码影响最小
4. **容错性好**：自动降级机制保证系统稳定
5. **统一接口**：与 matcher 设计模式一致，易于理解和使用
