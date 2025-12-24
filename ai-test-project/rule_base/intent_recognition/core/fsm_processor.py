from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FSMProcessor:
    """
    有限状态机处理器（简化版本）：

    设计目标：
    - 作为低优先级兜底识别器
    - 将来可以接入大模型，根据上下文状态做更复杂决策
    - 当前实现：
      * 支持上下文感知，可延续上一轮意图
      * 可在后续版本中增强
    """

    def __init__(self, config):
        self.name = "fsm"
        self.priority = 50
        self.config = config

    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional['IntentResult']:
        """
        使用有限状态机解析文本意图。
        
        Args:
            text: 待识别的文本
            context: 上下文信息（可选），用于状态感知
            
        Returns:
            IntentResult 或 None
        
        注意：支持基于上下文的意图延续
        """
        from .rule_engine import IntentResult
        
        context = context or {}
        last_intent = context.get("last_intent")
        
        # 如果存在上下文且文本较短/模糊，尝试延续上一轮意图
        if last_intent and len(text.strip()) < 10:
            return IntentResult(
                intent=last_intent,
                confidence=0.4,
                recognizer=self.name,
                slots={},
                raw_matches={"source": "last_intent"},
                metadata={"fsm_reason": "continue_last_intent"},
            )
        
        # 其他情况返回 None，由其他识别器处理
        return None
