from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core.rule_engine import RuleEngine, IntentResult, BaseIntentRecognizer
from .core.slot_filler import BaseSlotFiller


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


class IntentEngine:
    """
    对外暴露的意图识别 + 槽位填充引擎封装。
    
    支持自定义识别器和槽位提取器的扩展。
    """

    def __init__(
        self,
        base_dir: str | Path | None = None,
        timeout_per_recognizer: float = 0.5,
        extra_recognizers: Optional[List[BaseIntentRecognizer]] = None,
        extra_slot_fillers: Optional[List[BaseSlotFiller]] = None,
    ):
        if base_dir is None:
            # 默认使用当前文件所在目录的 config
            base_dir = Path(__file__).resolve().parent
        base_dir = Path(base_dir)
        config_dir = base_dir / "config"

        self.engine = RuleEngine(
            config_dir=config_dir,
            text_processor=None,  # 预处理接口留给业务方实现
            timeout_per_recognizer=timeout_per_recognizer,
            extra_recognizers=extra_recognizers,
            extra_slot_fillers=extra_slot_fillers,
        )

    def handle(self, text: str, context: Dict[str, Any] | None = None) -> IntentResult:
        return self.engine.process(text, context or {})


def handle_user_input(text: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    便捷函数：直接返回 dict，适合对接上层服务。
    """
    engine = IntentEngine()
    result = engine.handle(text, context)

    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "recognizer": result.recognizer,
        "slots": result.slots,
        "metadata": result.metadata,
        "raw_matches": result.raw_matches,
    }


if __name__ == "__main__":
    # 简单命令行交互示例
    engine = IntentEngine()
    ctx: Dict[str, Any] = {}

    print("Rule-based Intent Recognition Demo (输入 q 退出)")
    while True:
        try:
            text = input("User> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if text.lower() in {"q", "quit", "exit"}:
            break

        result = engine.handle(text, ctx)
        # 将当前结果写入上下文，FSM 可使用
        ctx["last_intent"] = result.intent

        print(
            f"  Intent: {result.intent} (confidence={result.confidence:.2f}, via={result.recognizer})"
        )
        print(f"  Slots: {result.slots}")
        print(f"  Metadata: {result.metadata}")
        print()
