from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """
    关键词匹配器：

    keywords.json 规范示例：
    {
      "book_flight": {
        "keywords": ["机票", "航班", "飞机"],
        "must_keywords": [],
        "exclude_keywords": ["取消"],
        "weight": 1.0
      }
    }
    """

    def __init__(self, config):
        self.name = "keyword"
        self.priority = 80
        self.config = config
        self.keywords_conf: Dict[str, Any] = config.keywords or {}

    def _score_intent(self, text: str, conf: Dict[str, Any]) -> float:
        text_lower = text.lower()
        keywords = conf.get("keywords", [])
        must_keywords = conf.get("must_keywords", [])
        exclude_keywords = conf.get("exclude_keywords", [])
        weight = float(conf.get("weight", 1.0))

        # 排除词命中则直接 0
        for kw in exclude_keywords:
            if kw.lower() in text_lower:
                return 0.0

        # 必须词
        for kw in must_keywords:
            if kw.lower() not in text_lower:
                return 0.0

        if not keywords:
            return 0.0

        hit = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                hit += 1

        if hit == 0:
            return 0.0

        base = hit / len(keywords)
        confidence = min(base * weight, 0.85)  # 最高不超过 0.85
        return confidence

    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional['IntentResult']:
        """
        使用关键词匹配解析文本意图。
        
        Args:
            text: 待识别的文本
            context: 上下文信息（可选）
            
        Returns:
            IntentResult 或 None
        """
        from .rule_engine import IntentResult
        
        if not self.keywords_conf:
            return None

        best_intent: Optional[str] = None
        best_confidence = 0.0
        raw_scores: Dict[str, float] = {}

        for intent, conf in self.keywords_conf.items():
            score = self._score_intent(text, conf)
            raw_scores[intent] = score
            if score > best_confidence:
                best_confidence = score
                best_intent = intent

        if not best_intent or best_confidence <= 0.0:
            return None

        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            recognizer=self.name,
            slots={},
            raw_matches={"scores": raw_scores},
            metadata={},
        )
