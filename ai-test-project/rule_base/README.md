# 规则驱动意图识别与槽位填充框架

## 概述

这是一个**工业级**的规则驱动意图识别和槽位填充框架，支持：

- ✅ 多策略并行识别（正则/关键词/FSM）
- ✅ 超时控制与降级机制
- ✅ 槽位填充（正则 + 可选 LLM 兜底）
- ✅ 完全可扩展的架构
- ✅ 配置驱动，易于维护

## 架构设计

```
intent_recognition/
├── core/
│   ├── rule_engine.py          # 规则引擎核心（流程编排、结果融合）
│   ├── regex_matcher.py        # 正则匹配器（优先级: 高）
│   ├── keyword_matcher.py      # 关键词匹配器（优先级: 中）
│   ├── fsm_processor.py        # 有限状态机处理器（优先级: 低）
│   └── slot_filler.py          # 槽位填充器（正则 + LLM 兜底）
├── config/
│   ├── intents.json           # 意图定义与槽位配置
│   ├── keywords.json          # 关键词库配置
│   └── regex_patterns.json    # 正则模式配置
├── utils/
│   └── text_processor.py      # 文本预处理接口（仅定义）
└── main.py                    # 主入口文件
```

## 数据流

```
用户输入文本
    ↓
文本预处理 (可选)
    ↓
多策略并行识别
    ├── 正则匹配器 (优先级: 高)
    ├── 关键词匹配器 (优先级: 中)  
    └── 状态机处理器 (优先级: 低)
    ↓
结果融合与决策
    ↓
槽位填充 (正则提取 + LLM兜底)
    ↓
返回最终结果
```

## 快速开始

### 1. 基础使用

```python
from intent_recognition import IntentEngine

# 创建引擎实例
engine = IntentEngine()

# 识别意图
result = engine.handle("我想预订从北京到上海的机票")

print(f"意图: {result.intent}")              # book_flight
print(f"置信度: {result.confidence}")         # 0.9+
print(f"识别器: {result.recognizer}")         # regex
print(f"槽位: {result.slots}")               # {'departure_city': '北京', 'arrival_city': '上海'}
```

### 2. 带上下文的识别

```python
context = {}

# 第一轮
result1 = engine.handle("查询订单ABC12345678", context)
context["last_intent"] = result1.intent

# 第二轮 - FSM 可以利用上下文
result2 = engine.handle("状态怎么样", context)
```

### 3. 便捷函数

```python
from intent_recognition import handle_user_input

result = handle_user_input("从北京到上海的机票")
# 返回 dict 格式，方便对接 API
```

## 配置说明

### intents.json

定义意图及其槽位：

```json
{
  "unknown_intent": "unknown",
  "intents": [
    {
      "name": "book_flight",
      "description": "预订机票",
      "priority": 100,
      "slots": [
        {"name": "departure_city", "required": true, "type": "str"},
        {"name": "arrival_city", "required": true, "type": "str"},
        {"name": "departure_date", "required": true, "type": "date"}
      ]
    }
  ]
}
```

### keywords.json

配置关键词匹配规则：

```json
{
  "book_flight": {
    "keywords": ["机票", "航班", "飞机", "预订"],
    "must_keywords": [],
    "exclude_keywords": ["取消", "退票"],
    "weight": 1.0
  }
}
```

### regex_patterns.json

配置正则匹配模式（意图 + 槽位）：

```json
{
  "intents": {
    "book_flight": [
      {
        "pattern": "从(?P<departure_city>.+?)到(?P<arrival_city>.+?)的机票",
        "flags": "i"
      }
    ]
  },
  "slots": {
    "departure_date": [
      {
        "pattern": "(?P<departure_date>\\d{4}-\\d{1,2}-\\d{1,2})",
        "flags": "i"
      }
    ]
  }
}
```

## 核心特性

### 1. 结果融合策略

```
1. 优先级策略: 正则匹配 > 关键词匹配 > 其他
2. 置信度阈值: 正则匹配置信度 > 0.8 时直接采用
3. 最优选择: 其他情况选择置信度最高的结果
4. 兜底机制: 无有效结果时返回未知意图
```

### 2. 超时与降级

```python
# 设置单个识别器的超时时间
engine = IntentEngine(timeout_per_recognizer=0.5)

# 超时策略会被自动降级，不影响其他识别器
```

### 3. 槽位填充

- **正则精确匹配**：从 `regex_patterns.json` 的 `slots` 部分提取
- **LLM 兜底**（可选）：实现 `BaseLLMSlotFiller` 接口

```python
from intent_recognition.core.slot_filler import BaseLLMSlotFiller

class MyLLMFiller(BaseLLMSlotFiller):
    def fill_missing_slots(self, text, intent_name, current_slots):
        # 调用你的 LLM 服务
        return {"missing_slot": "extracted_value"}

# 创建引擎时注入
engine = IntentEngine()
engine.engine.slot_filler.llm_filler = MyLLMFiller()
```

## 扩展指南

### 1. 添加自定义识别器

```python
from intent_recognition.core.rule_engine import BaseIntentRecognizer, IntentResult

class MyCustomRecognizer(BaseIntentRecognizer):
    def __init__(self, config):
        super().__init__(name="custom", priority=70)
        self.config = config
    
    def recognize(self, text, context=None):
        # 实现你的识别逻辑
        if "特定条件" in text:
            return IntentResult(
                intent="custom_intent",
                confidence=0.75,
                recognizer=self.name,
                slots={},
                raw_matches={},
                metadata={}
            )
        return None

# 注入到引擎
from intent_recognition.core.rule_engine import RuleEngine
engine = RuleEngine(
    config_dir="./config",
    extra_recognizers=[MyCustomRecognizer(config)]
)
```

### 2. 实现文本预处理

```python
from intent_recognition.utils.text_processor import BaseTextProcessor

class MyTextProcessor(BaseTextProcessor):
    def preprocess(self, text, context=None):
        # 去除标点、全角转半角等
        return text.strip().lower()

# 使用
from intent_recognition.core.rule_engine import RuleEngine
engine = RuleEngine(
    config_dir="./config",
    text_processor=MyTextProcessor()
)
```

### 3. 扩展配置格式

所有配置都是 JSON 格式，完全可以根据业务需求扩展字段：

```json
{
  "book_flight": {
    "keywords": ["机票"],
    "weight": 1.0,
    "custom_field": "your_custom_value"
  }
}
```

在识别器中读取：

```python
conf = self.config.keywords.get("book_flight")
custom_value = conf.get("custom_field")
```

## 测试

运行测试示例：

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base
python test_intent_recognition.py
```

或者交互式测试：

```bash
cd intent_recognition
python main.py
```

## 设计理念

1. **低侵入性**：框架对业务代码零侵入，通过配置文件管理规则
2. **高扩展性**：所有组件都可插拔，支持自定义识别器和处理器
3. **工业级可靠性**：
   - 超时控制防止单个策略阻塞
   - 降级机制保证系统稳定性
   - 完善的日志记录便于调试
4. **配置驱动**：规则变更无需修改代码，只需更新 JSON 配置

## API 参考

### IntentResult

```python
@dataclass
class IntentResult:
    intent: str                    # 识别到的意图
    confidence: float              # 置信度 [0-1]
    recognizer: str                # 识别器名称
    slots: Dict[str, Any]          # 提取的槽位
    raw_matches: Dict[str, Any]    # 原始匹配结果
    metadata: Dict[str, Any]       # 元数据
```

### IntentEngine

```python
class IntentEngine:
    def __init__(
        self,
        base_dir: str | Path | None = None,  # 配置目录父路径
        timeout_per_recognizer: float = 0.5,  # 单个识别器超时
    )
    
    def handle(
        self,
        text: str,                    # 用户输入
        context: Dict[str, Any] | None = None  # 上下文
    ) -> IntentResult
```

## 许可证

MIT License
