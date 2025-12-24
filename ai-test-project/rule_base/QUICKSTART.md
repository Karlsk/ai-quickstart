# 快速开始指南

## 框架已实现的功能

✅ **完整的目录结构**
```
intent_recognition/
├── __init__.py                 # 包入口
├── main.py                     # 主入口文件
├── core/                       # 核心模块
│   ├── __init__.py
│   ├── rule_engine.py         # 规则引擎（流程编排、结果融合）
│   ├── regex_matcher.py       # 正则匹配器（优先级 100）
│   ├── keyword_matcher.py     # 关键词匹配器（优先级 80）
│   ├── fsm_processor.py       # FSM 处理器（优先级 50）
│   └── slot_filler.py         # 槽位填充器
├── config/                     # 配置文件
│   ├── intents.json           # 意图定义
│   ├── keywords.json          # 关键词库
│   └── regex_patterns.json    # 正则模式
└── utils/                      # 工具模块
    ├── __init__.py
    └── text_processor.py      # 文本预处理接口
```

✅ **核心特性**
- 多策略并行识别（正则/关键词/FSM）
- 超时控制与降级机制（每个识别器独立超时）
- 智能结果融合（优先级 + 置信度）
- 槽位填充（正则精确匹配 + LLM 兜底接口）
- 完全可扩展架构
- 配置驱动，低侵入性

## 立即测试

### 1. 基础功能测试

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base
python test_intent_recognition.py
```

**测试内容：**
- ✅ 正则匹配：从北京到上海的机票
- ✅ 关键词匹配：订单查询
- ✅ FSM 上下文感知
- ✅ 槽位填充：城市、日期、订单号
- ✅ 超时降级机制

### 2. 高级扩展测试

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/rule_base
python test_advanced.py
```

**测试内容：**
- ✅ 自定义识别器（ML 模型示例）
- ✅ LLM 槽位填充兜底
- ✅ 文本预处理器
- ✅ 综合使用所有扩展

### 3. 交互式测试

```bash
cd intent_recognition
python main.py
```

然后输入：
```
从北京到上海的机票
查询订单ABC12345678
我要投诉
q  # 退出
```

## 使用示例

### 最简单的使用

```python
from intent_recognition import handle_user_input

result = handle_user_input("从北京到上海的机票")
print(result)
# {
#   'intent': 'book_flight',
#   'confidence': 0.97,
#   'recognizer': 'regex',
#   'slots': {'departure_city': '北京', 'arrival_city': '上海'},
#   'metadata': {...}
# }
```

### 完整使用（带上下文）

```python
from intent_recognition import IntentEngine

engine = IntentEngine()
context = {}

# 第一轮
result1 = engine.handle("查询订单ABC12345678", context)
context["last_intent"] = result1.intent

# 第二轮 - FSM 会利用上下文
result2 = engine.handle("状态如何", context)
```

## 扩展框架

### 1. 添加新意图

编辑 `config/intents.json`：
```json
{
  "name": "refund_request",
  "description": "退款申请",
  "priority": 80,
  "slots": [
    {"name": "order_id", "required": true, "type": "str"}
  ]
}
```

编辑 `config/keywords.json`：
```json
"refund_request": {
  "keywords": ["退款", "退钱", "申请退款"],
  "must_keywords": [],
  "exclude_keywords": [],
  "weight": 1.0
}
```

编辑 `config/regex_patterns.json`：
```json
"refund_request": [
  {
    "pattern": "申请退款订单(?P<order_id>\\w+)",
    "flags": "i"
  }
]
```

### 2. 添加自定义识别器

```python
from intent_recognition.core.rule_engine import BaseIntentRecognizer, IntentResult

class MyRecognizer(BaseIntentRecognizer):
    def __init__(self, config):
        super().__init__(name="my_recognizer", priority=70)
        self.config = config
    
    def recognize(self, text, context=None):
        # 你的识别逻辑
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

# 使用
from intent_recognition.core.rule_engine import RuleEngine
engine = RuleEngine(
    config_dir="./config",
    extra_recognizers=[MyRecognizer(config)]
)
```

### 3. 接入 LLM 槽位兜底

```python
from intent_recognition.core.slot_filler import BaseLLMSlotFiller

class MyLLMFiller(BaseLLMSlotFiller):
    def fill_missing_slots(self, text, intent_name, current_slots):
        # 调用你的 LLM API
        # result = call_llm_api(text, intent_name, current_slots)
        return {"missing_slot": "extracted_value"}

# 使用
engine = IntentEngine()
engine.engine.slot_filler.llm_filler = MyLLMFiller()
```

## 已实现的测试用例

运行 `test_intent_recognition.py` 后看到的结果：

```
✅ 输入: 我想预订从北京到上海的机票
   意图: book_flight (置信度: 0.97, 识别器: regex)
   槽位: {'departure_city': '北京', 'arrival_city': '上海'}

✅ 输入: 12月25日从深圳飞广州
   意图: book_flight (置信度: 1.00, 识别器: regex)
   槽位: {'departure_date': '12月25日', 'departure_city': '深圳', 'arrival_city': '广州'}

✅ 输入: 查询订单ABC12345678
   意图: query_order (置信度: 1.00, 识别器: regex)
   槽位: {'order_id': 'ABC12345678'}

✅ 输入: 取消订单XYZ98765432
   意图: cancel_order (置信度: 1.00, 识别器: regex)
   槽位: {'order_id': 'XYZ98765432'}

✅ 输入: 帮我查看我的订单状态
   意图: query_order (置信度: 0.75, 识别器: keyword)
   槽位: {}

✅ 输入: 随便说点什么
   意图: unknown (置信度: 0.00, 识别器: system)
   槽位: {}
```

## 工业级特性

### 1. 超时控制
```python
# 每个识别器独立超时
engine = IntentEngine(timeout_per_recognizer=0.5)
```

### 2. 降级机制
- 识别器超时 → 自动降级，记录日志
- 识别器异常 → 自动降级，记录日志
- LLM 超时 → 自动降级，使用正则结果

### 3. 结果融合策略
1. 正则匹配置信度 > 0.8 → 直接采用
2. 否则选择置信度最高的结果
3. 无有效结果 → 返回 unknown

### 4. 日志记录
所有异常、超时、降级都会记录日志，方便调试：
```
2025-12-15 [WARNING] Recognizer regex timed out, degraded.
```

## 配置说明

### intents.json 格式
```json
{
  "unknown_intent": "unknown",  // 未知意图的名称
  "intents": [
    {
      "name": "intent_name",
      "description": "描述",
      "priority": 100,
      "slots": [
        {
          "name": "slot_name",
          "required": true,      // 是否必填
          "type": "str"          // 类型（预留）
        }
      ]
    }
  ]
}
```

### keywords.json 格式
```json
{
  "intent_name": {
    "keywords": ["关键词1", "关键词2"],      // 匹配关键词
    "must_keywords": ["必须词"],            // 必须出现的词
    "exclude_keywords": ["排除词"],         // 排除的词
    "weight": 1.0                          // 权重系数
  }
}
```

### regex_patterns.json 格式
```json
{
  "intents": {
    "intent_name": [
      {
        "pattern": "正则表达式(?P<slot_name>...)",
        "flags": "i"  // i=忽略大小写
      }
    ]
  },
  "slots": {
    "slot_name": [
      {
        "pattern": "(?P<slot_name>正则)",
        "flags": "i"
      }
    ]
  }
}
```

## 下一步

1. **根据业务调整配置**
   - 修改 `config/` 下的 JSON 文件
   - 添加你的业务意图和规则

2. **接入真实 LLM**
   - 实现 `BaseLLMSlotFiller`
   - 调用 OpenAI / Claude / 本地模型

3. **添加更多识别器**
   - ML 分类模型
   - BERT 意图识别
   - 其他业务规则

4. **对接你的服务**
   - FastAPI / Flask 封装
   - gRPC 服务
   - 消息队列

## 支持

详细文档请查看：
- [README.md](README.md) - 完整文档
- [test_intent_recognition.py](test_intent_recognition.py) - 基础测试
- [test_advanced.py](test_advanced.py) - 高级扩展

祝你使用愉快！🎉
