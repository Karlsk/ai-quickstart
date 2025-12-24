from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RegexMatcher:
    """
    正则匹配器：
    - 从 regex_patterns.json 中加载规则
    - patterns:
        {
          "intents": {
            "book_flight": [
              {"pattern": "预订(?P<destination>.+?)的机票", "flags": "i"}
            ]
          }
        }
    """

    def __init__(self, config):
        self.name = "regex"
        self.priority = 100
        self.config = config
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        patterns_conf = self.config.regex_patterns.get("intents", {})
        for intent, patterns in patterns_conf.items():
            compiled_list: List[re.Pattern] = []
            for p in patterns:
                pattern = p.get("pattern")
                flags_str = p.get("flags", "")
                flags = 0
                if "i" in flags_str.lower():
                    flags |= re.IGNORECASE
                if pattern:
                    compiled_list.append(re.compile(pattern, flags))
            self._compiled_patterns[intent] = compiled_list

    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional['IntentResult']:
        """
        使用正则匹配解析文本意图。
        
        Args:
            text: 待识别的文本
            context: 上下文信息（可选）
            
        Returns:
            IntentResult 或 None
        """
        # 需要导入 IntentResult，为避免循环导入，在函数内导入
        from .rule_engine import IntentResult
        
        if not self._compiled_patterns:
            return None

        best_intent: Optional[str] = None
        best_confidence = 0.0
        best_groups: Dict[str, Any] = {}
        all_matches: Dict[str, Any] = {}

        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    groups = match.groupdict()
                    confidence = 0.9  # 正则命中基础置信度
                    # 简单根据匹配长度微调
                    confidence += min(len(match.group(0)) / max(len(text), 1) * 0.1, 0.1)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
                        best_groups = groups
                    all_matches.setdefault(intent, []).append(
                        {"pattern": pattern.pattern, "groups": groups}
                    )

        if not best_intent:
            return None

        return IntentResult(
            intent=best_intent,
            confidence=min(best_confidence, 1.0),
            recognizer=self.name,
            slots=best_groups,
            raw_matches=all_matches,
            metadata={},
        )
