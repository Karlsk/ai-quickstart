from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .regex_matcher import RegexMatcher
from .keyword_matcher import KeywordMatcher
from .fsm_processor import FSMProcessor
from .slot_filler import SlotFiller, BaseSlotFiller
from ..utils.text_processor import BaseTextProcessor


logger = logging.getLogger(__name__)


UNKNOWN_INTENT = "unknown"


@dataclass
class IntentResult:
    intent: str
    confidence: float
    recognizer: str
    slots: Dict[str, Any] = field(default_factory=dict)
    raw_matches: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """
    负责加载 config/ 下的所有 JSON 配置文件。
    
    自动加载配置目录下的所有 .json 文件，并将配置内容存储为属性。
    例如：
    - intents.json -> self.intents
    - keywords.json -> self.keywords
    - regex_patterns.json -> self.regex_patterns
    - xw_excel.json -> self.xw_excel (顶层键) 或 self.excel_analyzer (如果文件中有该键)
    """

    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        self.intents: Dict[str, Any] = {}
        self.keywords: Dict[str, Any] = {}
        self.regex_patterns: Dict[str, Any] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}  # 缓存所有配置文件
        self._load_all()

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.config_dir / filename
        if not path.exists():
            logger.warning("Config file not found: %s", path)
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_all(self) -> None:
        """自动加载配置目录下的所有 JSON 文件"""
        # 加载固定的配置文件（保持向后兼容）
        self.intents = self._load_json("intents.json")
        self.keywords = self._load_json("keywords.json")
        self.regex_patterns = self._load_json("regex_patterns.json")
        
        # 自动发现并加载所有 JSON 文件
        if not self.config_dir.exists():
            logger.warning("Config directory not found: %s", self.config_dir)
            return
        
        for json_file in self.config_dir.glob("*.json"):
            filename = json_file.stem  # 去掉 .json 后缀
            config_data = self._load_json(json_file.name)
            
            # 缓存原始数据
            self._config_cache[filename] = config_data
            
            # 将配置数据的顶层键设置为 ConfigManager 的属性
            # 例如: xw_excel.json 中的 {"excel_analyzer": {...}} 
            # 会创建 self.excel_analyzer 属性
            if isinstance(config_data, dict):
                for key, value in config_data.items():
                    if not hasattr(self, key):
                        setattr(self, key, value)
            
            logger.debug("Loaded config file: %s", json_file.name)

    def reload(self) -> None:
        self._load_all()

    def get_intent_def(self, intent_name: str) -> Optional[Dict[str, Any]]:
        intents = self.intents.get("intents", [])
        for item in intents:
            if item.get("name") == intent_name:
                return item
        return None

    def get_intent_slots(self, intent_name: str) -> List[Dict[str, Any]]:
        intent_def = self.get_intent_def(intent_name)
        if not intent_def:
            return []
        return intent_def.get("slots", [])

    def get_unknown_intent_name(self) -> str:
        return self.intents.get("unknown_intent", UNKNOWN_INTENT)


class BaseIntentRecognizer:
    """
    通用意图识别器基类，所有识别策略需实现 parse 方法。
    """

    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority

    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional[IntentResult]:
        """
        解析文本，返回意图识别结果。
        
        Args:
            text: 待识别的文本
            context: 上下文信息（可选），用于多轮对话或状态感知
            
        Returns:
            IntentResult 或 None（未识别到意图时）
        """
        raise NotImplementedError


class RuleEngine:
    """
    整体规则引擎：
    - 完整执行流程：
        文本预处理 ->
        多策略并行识别 ->
        结果融合 ->
        槽位填充 ->
        返回最终结果
    - 支持：
        * 策略扩展
        * 识别超时控制
        * 策略降级（跳过超时/异常策略）
        * 多槽位提取器配置
    """

    def __init__(
        self,
        config_dir: str | Path,
        text_processor: BaseTextProcessor | None = None,
        timeout_per_recognizer: float = 0.5,
        max_workers: int = 4,
        extra_recognizers: Optional[List[BaseIntentRecognizer]] = None,
        extra_slot_fillers: Optional[List[BaseSlotFiller]] = None,
    ):
        self.config = ConfigManager(config_dir)
        self.text_processor = text_processor
        self.timeout_per_recognizer = timeout_per_recognizer
        self.max_workers = max_workers

        # 内置三种策略
        recognizers: List[BaseIntentRecognizer] = [
            RegexMatcher(self.config),
            KeywordMatcher(self.config),
            FSMProcessor(self.config),
        ]

        if extra_recognizers:
            recognizers.extend(extra_recognizers)
        self.recognizers = recognizers

        # 槽位提取器：默认使用 SlotFiller，支持扩展
        slot_fillers: List[BaseSlotFiller] = [SlotFiller(self.config)]
        if extra_slot_fillers:
            slot_fillers.extend(extra_slot_fillers)
        self.slot_fillers = slot_fillers
        
        # 为了向后兼容，保留 slot_filler 属性
        self.slot_filler = slot_fillers[0]

    # ===== 对外主入口 =====
    def process(self, text: str, context: Dict[str, Any] | None = None) -> IntentResult:
        """
        对外统一入口：输入原始文本，返回最终 IntentResult。
        
        支持通过 context 指定槽位提取器：
        context = {
            "slot_filler": "custom_filler_name"  # 指定使用的槽位提取器名称
        }
        如果未指定或找不到，默认使用第一个槽位提取器（SlotFiller）
        """
        if context is None:
            context = {}

        preprocessed = self._preprocess(text, context)
        raw_results = self._run_recognizers(preprocessed, context)
        fused = self._fuse_results(raw_results)
        final_result = self._fill_slots(fused, text, context)
        return final_result

    # ===== 内部步骤实现 =====
    def _preprocess(self, text: str, context: Dict[str, Any]) -> str:
        if self.text_processor:
            try:
                return self.text_processor.preprocess(text, context)
            except Exception:
                logger.exception("Text preprocess failed, fallback to raw text.")
                return text
        # 默认简单处理，可根据需要扩展
        return text.strip()

    def _run_recognizers(self, text: str, context: Dict[str, Any]) -> List[IntentResult]:
        """
        并行运行各识别策略，支持超时和降级：
        - 每个识别器有单独 timeout_per_recognizer
        - 超时/异常：记录日志并降级为"忽略该策略结果"
        """
        results: List[IntentResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_recognizer = {
                executor.submit(recognizer.parse, text, context): recognizer
                for recognizer in self.recognizers
            }

            for future, recognizer in future_to_recognizer.items():
                try:
                    result = future.result(timeout=self.timeout_per_recognizer)
                    if result is not None:
                        results.append(result)
                except FuturesTimeoutError:
                    logger.warning("Recognizer %s timed out, degraded.", recognizer.name)
                except Exception:
                    logger.exception("Recognizer %s failed, degraded.", recognizer.name)

        return results

    def _fuse_results(self, results: List[IntentResult]) -> IntentResult:
        """
        结果融合策略：
        1. 优先级策略: 正则匹配 > 关键词匹配 > 其他
        2. 置信度阈值: 正则匹配置信度 > 0.8 时直接采用
        3. 最优选择: 其他情况选择置信度最高的结果
        4. 兜底机制: 无有效结果时返回未知意图
        """
        if not results:
            return self._build_unknown_result(reason="no_valid_result")

        # 1. 正则匹配优先
        regex_results = [r for r in results if r.recognizer == "regex"]
        if regex_results:
            best_regex = max(regex_results, key=lambda r: r.confidence)
            if best_regex.confidence >= 0.8:
                best_regex.metadata.setdefault("fusion_reason", "regex_confidence_over_0.8")
                return best_regex

        # 2. 其他情况，选置信度最高
        best_overall = max(results, key=lambda r: r.confidence)
        best_overall.metadata.setdefault("fusion_reason", "max_confidence")
        return best_overall

    def _build_unknown_result(self, reason: str) -> IntentResult:
        return IntentResult(
            intent=self.config.get_unknown_intent_name(),
            confidence=0.0,
            recognizer="system",
            slots={},
            raw_matches={},
            metadata={"reason": reason},
        )

    def _fill_slots(self, intent_result: IntentResult, original_text: str, context: Dict[str, Any]) -> IntentResult:
        """
        槽位填充：
        1. 从 context 中获取指定的槽位提取器名称
        2. 如果未指定或找不到，使用默认的槽位提取器
        3. 调用选定的槽位提取器进行槽位填充
        """
        specified_filler_name = context.get("slot_filler")
        
        # 选择槽位提取器
        selected_filler = self.slot_fillers[0]  # 默认使用第一个
        
        if specified_filler_name:
            for filler in self.slot_fillers:
                if filler.name == specified_filler_name:
                    selected_filler = filler
                    logger.debug("Using specified slot filler: %s", specified_filler_name)
                    break
            else:
                logger.warning(
                    "Specified slot filler '%s' not found, using default: %s",
                    specified_filler_name,
                    selected_filler.name
                )
        
        return selected_filler.fill_slots(intent_result, original_text, context)
