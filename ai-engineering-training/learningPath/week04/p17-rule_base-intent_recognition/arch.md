# 项目目录
intent_recognition/
├── core/
│   ├── rule_engine.py          # 规则引擎核心
│   ├── regex_matcher.py        # 正则匹配器
│   ├── keyword_matcher.py      # 关键词匹配器
│   ├── fsm_processor.py        # 有限状态机处理器
│   └── slot_filler.py          # 槽位填充器
├── config/
│   ├── intents.json           # 意图配置
│   ├── keywords.json          # 关键词库
│   └── regex_patterns.json    # 正则模式
├── utils/
│   └── text_processor.py      # 文本预处理工具
└── main.py                    # 主入口文件

# 数据流
整体执行流程

用户输入文本
    ↓
文本预处理 (去除标点、转小写等)
    ↓
多策略并行识别
    ├── 正则匹配器 (优先级: 高)
    ├── 关键词匹配器 (优先级: 中)  
    └── 状态机处理器 (优先级: 低)
    ↓
结果融合与决策
    ↓
槽位填充 (提取参数)
    ↓
返回最终结果
