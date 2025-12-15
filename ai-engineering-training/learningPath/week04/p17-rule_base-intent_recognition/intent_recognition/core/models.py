from typing import List, Optional
from dataclasses import dataclass

@dataclass
class IntentResult:
    """
    意图识别结果数据类
    ================

    用于封装单个解析器的识别结果，包含以下信息:
    - intent: 识别出的意图类型 (如 'query_order', 'refund' 等)
    - confidence: 置信度分数 (0.0-1.0)
    - matched_rules: 匹配的规则列表 (用于可解释性)
    - extracted_entities: 提取的实体信息 (如订单号、时间等)
    """
    intent: str = "unknown"                    # 默认为未知意图
    confidence: float = 0.0                    # 默认置信度为0
    matched_rules: List[str] = None            # 匹配的规则列表
    extracted_entities: Optional[tuple] = None # 提取的实体元组

    def __post_init__(self):
        """数据类初始化后处理，确保 matched_rules 不为 None"""
        if self.matched_rules is None:
            self.matched_rules = []