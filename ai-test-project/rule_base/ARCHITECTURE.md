# 意图识别与槽位填充框架 - 架构设计文档

## 1. 架构概览

### 1.1 设计理念

- **低侵入性**：遵循用户偏好，对客户端代码零侵入，所有规则通过配置文件管理
- **工业级可靠性**：超时控制、降级机制、完善的错误处理
- **高扩展性**：所有组件可插拔，支持自定义扩展
- **配置驱动**：规则变更无需修改代码，只需更新 JSON 配置

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        IntentEngine                          │
│                      (对外统一接口)                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                       RuleEngine                             │
│                    (核心流程编排)                              │
├─────────────────────────────────────────────────────────────┤
│  1. 文本预处理 (TextProcessor - 可选)                         │
│  2. 多策略并行识别 (ThreadPoolExecutor)                       │
│  3. 结果融合 (Priority + Confidence)                         │
│  4. 槽位填充 (SlotFiller)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Regex   │  │Keyword  │  │  FSM    │  ... 可扩展更多识别器
│Matcher  │  │Matcher  │  │Processor│
│(P:100)  │  │(P:80)   │  │(P:50)   │
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     └────────────┼────────────┘
                  ▼
          ┌──────────────┐
          │ IntentResult │
          └──────────────┘
                  │
                  ▼
          ┌──────────────┐
          │ SlotFiller   │
          │ - Regex提取   │
          │ - LLM兜底    │
          └──────────────┘
```

## 2. 核心组件

### 2.1 RuleEngine（规则引擎核心）

**职责：**
- 流程编排：文本预处理 → 并行识别 → 结果融合 → 槽位填充
- 识别器管理：支持内置和自定义识别器
- 超时控制：每个识别器独立超时设置
- 降级策略：识别器超时/异常时自动降级

**关键方法：**
```python
def process(text, context) -> IntentResult:
    preprocessed = _preprocess(text)           # 1. 预处理
    raw_results = _run_recognizers(preprocessed)  # 2. 并行识别
    fused = _fuse_results(raw_results)        # 3. 融合
    final = slot_filler.fill_slots(fused)     # 4. 槽位填充
    return final
```

**并行执行机制：**
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(recognizer.recognize, text, context): recognizer
        for recognizer in self.recognizers
    }
    for future in futures:
        try:
            result = future.result(timeout=0.5)  # 单个超时
        except TimeoutError:
            logger.warning("降级")  # 自动降级
```

### 2.2 识别器架构

#### 基类设计
```python
class BaseIntentRecognizer:
    def __init__(self, name: str, priority: int):
        self.name = name        # 识别器名称
        self.priority = priority  # 优先级（仅作参考）
    
    def recognize(self, text, context) -> Optional[IntentResult]:
        raise NotImplementedError
```

#### 内置识别器

| 识别器 | 优先级 | 说明 | 使用场景 |
|--------|--------|------|----------|
| RegexMatcher | 100 | 正则匹配，精确度高 | 结构化输入、明确模式 |
| KeywordMatcher | 80 | 关键词匹配，覆盖面广 | 模糊意图、关键词触发 |
| FSMProcessor | 50 | 有限状态机，上下文感知 | 多轮对话、状态延续 |

### 2.3 结果融合策略

```python
def _fuse_results(results: List[IntentResult]) -> IntentResult:
    """
    融合策略：
    1. 正则匹配优先：置信度 > 0.8 直接采用
    2. 最优选择：选择置信度最高的结果
    3. 兜底机制：无有效结果返回 unknown
    """
    if not results:
        return build_unknown_result()
    
    # 1. 正则优先
    regex_results = [r for r in results if r.recognizer == "regex"]
    if regex_results:
        best = max(regex_results, key=lambda r: r.confidence)
        if best.confidence >= 0.8:
            return best
    
    # 2. 最优选择
    return max(results, key=lambda r: r.confidence)
```

### 2.4 槽位填充架构

**两级填充策略：**

```
┌────────────────────────────────────────────┐
│          SlotFiller (槽位填充器)             │
├────────────────────────────────────────────┤
│                                            │
│  第一级：正则精确匹配                        │
│  ├─ 从 regex_patterns.json 加载槽位规则    │
│  ├─ 对每个必填槽位做正则提取                │
│  └─ 高精度、零延迟                          │
│                                            │
│  第二级：LLM 兜底（可选）                    │
│  ├─ 检测缺失的必填槽位                      │
│  ├─ 调用 LLM API 进行智能提取              │
│  ├─ 超时控制（默认 2s）                     │
│  └─ 超时/异常自动降级                       │
│                                            │
└────────────────────────────────────────────┘
```

## 3. 配置系统

### 3.1 配置文件设计

```
config/
├── intents.json          # 意图定义（意图列表、槽位定义）
├── keywords.json         # 关键词库（关键词、排除词、权重）
└── regex_patterns.json   # 正则模式（意图正则、槽位正则）
```

### 3.2 配置规范

#### intents.json
```json
{
  "unknown_intent": "unknown",
  "intents": [
    {
      "name": "意图名称",
      "description": "描述",
      "priority": 100,
      "slots": [
        {
          "name": "槽位名",
          "required": true,
          "type": "类型"
        }
      ]
    }
  ]
}
```

**扩展性：**
- 可添加自定义字段（如 `category`, `tags`）
- 可定义槽位验证规则（如 `pattern`, `enum`）

#### keywords.json
```json
{
  "intent_name": {
    "keywords": ["关键词"],      // 匹配词
    "must_keywords": [],         // 必须词
    "exclude_keywords": [],      // 排除词
    "weight": 1.0               // 权重
  }
}
```

**匹配逻辑：**
```python
score = (hit_count / total_keywords) * weight
confidence = min(score, 0.85)  # 最高不超过 0.85
```

#### regex_patterns.json
```json
{
  "intents": {
    "intent_name": [
      {
        "pattern": "正则(?P<slot>...)",
        "flags": "i"
      }
    ]
  },
  "slots": {
    "slot_name": [
      {
        "pattern": "(?P<slot_name>...)",
        "flags": "i"
      }
    ]
  }
}
```

## 4. 数据流详解

### 4.1 完整数据流

```
用户输入: "预订2024-12-25从北京到上海的机票"
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. 文本预处理 (可选)                     │
│    - 去除空格、标点                      │
│    - 全角转半角                          │
│    - 繁简转换等                          │
└────────────┬────────────────────────────┘
             ▼
┌─────────────────────────────────────────┐
│ 2. 多策略并行识别 (ThreadPool)           │
│                                         │
│ ┌─────────────┐  ┌──────────────┐      │
│ │RegexMatcher │  │KeywordMatcher│      │
│ │命中: ✓      │  │命中: ✓       │      │
│ │conf: 0.97   │  │conf: 0.60    │      │
│ │slots: {...} │  │slots: {}     │      │
│ └─────────────┘  └──────────────┘      │
│                                         │
│ ┌──────────────┐                        │
│ │FSMProcessor  │                        │
│ │命中: ✗       │                        │
│ └──────────────┘                        │
└────────────┬────────────────────────────┘
             ▼
┌─────────────────────────────────────────┐
│ 3. 结果融合                              │
│    - RegexMatcher: 0.97 > 0.8 → 采用    │
│    - 意图: book_flight                  │
│    - 槽位: {departure_city: 北京,       │
│             arrival_city: 上海,         │
│             departure_date: 2024-12-25} │
└────────────┬────────────────────────────┘
             ▼
┌─────────────────────────────────────────┐
│ 4. 槽位填充                              │
│    - 检查必填槽位                        │
│    - departure_city: ✓                  │
│    - arrival_city: ✓                    │
│    - departure_date: ✓                  │
│    - 无缺失，跳过 LLM 兜底               │
└────────────┬────────────────────────────┘
             ▼
        IntentResult
        {
          intent: "book_flight",
          confidence: 0.97,
          recognizer: "regex",
          slots: {...},
          metadata: {...}
        }
```

## 5. 扩展机制

### 5.1 自定义识别器

```python
class CustomRecognizer(BaseIntentRecognizer):
    def __init__(self, config):
        super().__init__(name="custom", priority=70)
    
    def recognize(self, text, context):
        # 自定义逻辑
        return IntentResult(...)

# 注入
engine = RuleEngine(
    config_dir="./config",
    extra_recognizers=[CustomRecognizer(config)]
)
```

### 5.2 文本预处理器

```python
class CustomProcessor(BaseTextProcessor):
    def preprocess(self, text, context):
        # 自定义预处理
        return processed_text

engine = RuleEngine(
    config_dir="./config",
    text_processor=CustomProcessor()
)
```

### 5.3 LLM 槽位兜底

```python
class LLMFiller(BaseLLMSlotFiller):
    def fill_missing_slots(self, text, intent, slots):
        # 调用 LLM
        return filled_slots

slot_filler = SlotFiller(config, llm_filler=LLMFiller())
```

## 6. 可靠性保障

### 6.1 超时控制

- **识别器级别超时**：每个识别器独立超时（默认 0.5s）
- **LLM 超时**：槽位填充 LLM 调用超时（默认 2s）
- **超时降级**：超时识别器自动跳过，不影响其他识别器

### 6.2 异常处理

```python
try:
    result = recognizer.recognize(text)
except Exception:
    logger.exception("Recognizer failed, degraded")
    # 自动降级，继续处理其他识别器
```

### 6.3 日志记录

- **INFO**：正常识别流程
- **WARNING**：超时、降级事件
- **ERROR**：严重错误（不会导致系统崩溃）

## 7. 性能特性

### 7.1 并行执行

- 使用 `ThreadPoolExecutor` 并行执行所有识别器
- 默认 4 个 worker，可配置

### 7.2 配置缓存

- 配置文件仅在初始化时加载一次
- 支持 `config.reload()` 热重载

### 7.3 正则编译缓存

- 所有正则模式在初始化时预编译
- 避免运行时重复编译开销

## 8. 设计模式应用

### 8.1 策略模式（Strategy Pattern）

- `BaseIntentRecognizer` 定义策略接口
- 多个识别器实现不同策略
- `RuleEngine` 动态选择和组合策略

### 8.2 模板方法模式（Template Method）

- `RuleEngine.process()` 定义处理流程模板
- 各步骤可通过注入不同组件灵活定制

### 8.3 工厂模式（Factory Pattern）

- `ConfigManager` 负责配置对象的创建
- 识别器通过工厂方法创建和初始化

### 8.4 适配器模式（Adapter Pattern）

- `BaseLLMSlotFiller` 适配不同的 LLM 服务
- `BaseTextProcessor` 适配不同的文本处理工具

## 9. 总结

### 9.1 核心优势

1. **低侵入性**：符合用户偏好，配置驱动，代码无侵入
2. **高可靠性**：超时控制、降级机制、完善错误处理
3. **易扩展**：所有组件可插拔，支持自定义扩展
4. **工业级**：并行执行、缓存优化、日志完善

### 9.2 适用场景

- ✅ 客服系统意图识别
- ✅ 智能助手命令解析
- ✅ 聊天机器人意图分类
- ✅ 表单自动填充
- ✅ 任何需要意图识别 + 槽位填充的场景

### 9.3 后续扩展方向

1. 集成 ML 模型（BERT、FastText）
2. 支持多语言
3. 添加意图消歧模块
4. 支持槽位验证和归一化
5. 添加对话状态管理
