#!/usr/bin/env python3
"""
高级扩展示例：
1. 自定义识别器
2. LLM 槽位填充兜底
3. 文本预处理器
"""
import re
from typing import Any, Dict, Optional
from intent_recognition.core.rule_engine import BaseIntentRecognizer, IntentResult, RuleEngine
from intent_recognition.core.slot_filler import BaseLLMSlotFiller
from intent_recognition.utils.text_processor import BaseTextProcessor


# ========== 1. 自定义识别器示例 ==========
class MLModelRecognizer(BaseIntentRecognizer):
    """
    自定义识别器示例：模拟接入机器学习模型
    在实际应用中，这里可以调用你训练好的分类模型
    """
    
    def __init__(self, config, model_path=None):
        super().__init__(name="ml_model", priority=90)
        self.config = config
        self.model_path = model_path
        # 这里可以加载你的模型
        # self.model = load_model(model_path)
    
    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional[IntentResult]:
        """
        使用机器学习模型识别意图
        
        Args:
            text: 待识别的文本
            context: 上下文信息（可选）
            
        Returns:
            IntentResult 或 None
        """
        # 模拟模型预测
        # 实际使用时替换为: predictions = self.model.predict(text)
        
        # 这里只是示例
        if "投诉" in text or "不满意" in text:
            return IntentResult(
                intent="complaint",
                confidence=0.88,
                recognizer=self.name,
                slots={},
                raw_matches={"model_output": "complaint_detected"},
                metadata={"model_version": "v1.0"},
            )
        
        # 未识别时返回 None
        return None


# ========== 2. LLM 槽位填充兜底示例 ==========
class OpenAISlotFiller(BaseLLMSlotFiller):
    """
    使用 OpenAI API 作为槽位填充兜底
    实际使用时需要配置 API Key
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        # 这里可以初始化 OpenAI 客户端
        # self.client = OpenAI(api_key=api_key)
    
    def fill_missing_slots(
        self,
        text: str,
        intent_name: str,
        current_slots: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        使用 LLM 填充缺失的槽位
        """
        # 实际使用时的伪代码：
        # prompt = f"从这段文本中提取槽位：{text}\n意图：{intent_name}\n已有槽位：{current_slots}"
        # response = self.client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return parse_slots(response)
        
        # 这里只是模拟
        print(f"  [LLM兜底] 尝试填充缺失槽位...")
        print(f"  输入: {text}")
        print(f"  意图: {intent_name}")
        print(f"  已有槽位: {current_slots}")
        
        # 模拟 LLM 提取
        filled_slots = dict(current_slots)
        
        if intent_name == "book_flight":
            # 简单模拟：尝试从文本中提取缺失信息
            if "departure_city" not in filled_slots:
                match = re.search(r"从(\w+)", text)
                if match:
                    filled_slots["departure_city"] = match.group(1)
            
            if "arrival_city" not in filled_slots:
                match = re.search(r"到(\w+)", text)
                if match:
                    filled_slots["arrival_city"] = match.group(1)
        
        print(f"  LLM填充后: {filled_slots}")
        return filled_slots


# ========== 3. 文本预处理器示例 ==========
class SimpleTextProcessor(BaseTextProcessor):
    """
    简单文本预处理器：
    - 去除多余空格
    - 全角转半角（数字、字母）
    - 可扩展其他功能
    """
    
    def preprocess(self, text: str, context: dict[str, Any] | None = None) -> str:
        """文本预处理"""
        # 1. 去除首尾空格
        text = text.strip()
        
        # 2. 全角转半角（简化版）
        text = self._full_to_half(text)
        
        # 3. 统一多个空格为单个空格
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _full_to_half(self, text: str) -> str:
        """全角字符转半角"""
        result = []
        for char in text:
            code = ord(char)
            # 全角空格
            if code == 0x3000:
                result.append(' ')
            # 全角字符（除空格）
            elif 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            else:
                result.append(char)
        return ''.join(result)


# ========== 测试扩展功能 ==========
def test_custom_recognizer():
    """测试自定义识别器"""
    print("=" * 60)
    print("测试自定义识别器（ML 模型）")
    print("=" * 60)
    
    from pathlib import Path
    from intent_recognition.core.rule_engine import ConfigManager
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    config = ConfigManager(config_dir)
    
    # 创建引擎，注入自定义识别器
    ml_recognizer = MLModelRecognizer(config)
    engine = RuleEngine(
        config_dir=config_dir,
        extra_recognizers=[ml_recognizer]
    )
    
    # 测试
    test_texts = [
        "我要投诉你们的服务",
        "非常不满意这次的购买体验",
        "从北京到上海的机票",  # 不应该被 ML 识别器识别
    ]
    
    for text in test_texts:
        result = engine.process(text)
        print(f"\n输入: {text}")
        print(f"意图: {result.intent} (识别器: {result.recognizer}, 置信度: {result.confidence:.2f})")
        if result.metadata:
            print(f"元数据: {result.metadata}")


def test_llm_slot_filler():
    """测试 LLM 槽位填充兜底"""
    print("\n" + "=" * 60)
    print("测试 LLM 槽位填充兜底")
    print("=" * 60)
    
    from pathlib import Path
    from intent_recognition.core.rule_engine import ConfigManager, RuleEngine
    from intent_recognition.core.slot_filler import SlotFiller
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    config = ConfigManager(config_dir)
    
    # 创建带 LLM 兜底的槽位填充器
    llm_filler = OpenAISlotFiller()
    slot_filler = SlotFiller(config, llm_filler=llm_filler, llm_timeout=2.0)
    
    # 创建引擎并替换槽位填充器
    engine = RuleEngine(config_dir=config_dir)
    engine.slot_filler = slot_filler
    
    # 测试：这个输入正则可能无法完整提取所有槽位
    text = "我想订明天从北京飞上海"
    result = engine.process(text)
    
    print(f"\n输入: {text}")
    print(f"意图: {result.intent}")
    print(f"槽位: {result.slots}")


def test_text_processor():
    """测试文本预处理"""
    print("\n" + "=" * 60)
    print("测试文本预处理")
    print("=" * 60)
    
    from pathlib import Path
    from intent_recognition.core.rule_engine import RuleEngine
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    
    # 创建带预处理器的引擎
    processor = SimpleTextProcessor()
    engine = RuleEngine(
        config_dir=config_dir,
        text_processor=processor
    )
    
    # 测试全角、多余空格
    test_texts = [
        "从北京    到   上海的机票",  # 多余空格
        "从北京到上海的机票",  # 全角字符（示例）
    ]
    
    for text in test_texts:
        print(f"\n原始输入: '{text}'")
        processed = processor.preprocess(text)
        print(f"预处理后: '{processed}'")
        
        result = engine.process(text)
        print(f"意图: {result.intent}")
        print(f"槽位: {result.slots}")


def test_combined():
    """综合测试：所有扩展一起使用"""
    print("\n" + "=" * 60)
    print("综合测试：所有扩展功能")
    print("=" * 60)
    
    from pathlib import Path
    from intent_recognition.core.rule_engine import ConfigManager, RuleEngine
    from intent_recognition.core.slot_filler import SlotFiller
    
    config_dir = Path(__file__).parent / "intent_recognition" / "config"
    config = ConfigManager(config_dir)
    
    # 组合所有扩展
    ml_recognizer = MLModelRecognizer(config)
    processor = SimpleTextProcessor()
    llm_filler = OpenAISlotFiller()
    slot_filler = SlotFiller(config, llm_filler=llm_filler)
    
    engine = RuleEngine(
        config_dir=config_dir,
        text_processor=processor,
        extra_recognizers=[ml_recognizer]
    )
    engine.slot_filler = slot_filler
    
    # 测试
    test_cases = [
        "从北京到上海的机票",
        "我要投诉你们的服务态度",
        "查询订单ABC12345678",
    ]
    
    for text in test_cases:
        result = engine.process(text)
        print(f"\n输入: {text}")
        print(f"意图: {result.intent} (via {result.recognizer}, 置信度: {result.confidence:.2f})")
        print(f"槽位: {result.slots}")


if __name__ == "__main__":
    test_custom_recognizer()
    test_llm_slot_filler()
    test_text_processor()
    test_combined()
    
    print("\n" + "=" * 60)
    print("高级扩展测试完成!")
    print("=" * 60)
    print("\n提示：")
    print("1. MLModelRecognizer: 演示如何接入机器学习模型")
    print("2. OpenAISlotFiller: 演示如何使用 LLM 作为槽位填充兜底")
    print("3. SimpleTextProcessor: 演示文本预处理功能")
    print("4. 所有扩展都是可插拔的，不影响核心框架")
