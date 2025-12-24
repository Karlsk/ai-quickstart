from typing import Dict, Any, List

from .models import IntentResult
from .regex_matcher import RegexIntentParser
from .keyword_matcher import KeywordIntentParser
from .slot_filler import (SlotExtractor)

class RuleBasedIntentChain:
    """
    LangChain 风格的意图识别主链
    ===========================

    系统架构说明:
    - 采用 LangChain 的链式调用设计模式
    - 集成多个解析器组件，实现模块化架构
    - 支持并行处理和智能融合决策
    - 提供完整的意图识别和槽位填充功能

    核心特性:
    1. 多策略融合: 正则匹配 + 关键词匹配
    2. 智能决策: 基于置信度和规则优先级
    3. 槽位提取: 自动提取业务参数
    4. 可解释性: 提供详细的推理过程

    工作流程:
    输入文本 → 并行解析 → 结果融合 → 槽位提取 → 推理解释 → 输出结果
    """

    def __init__(self):
        """
        初始化意图识别链的各个组件

        组件说明:
        - regex_parser: 正则表达式解析器，处理结构化输入
        - keyword_parser: 关键词解析器，处理自然语言输入
        - slot_extractor: 槽位提取器，提取业务参数

        设计优势:
        - 组件解耦: 各解析器独立工作，便于维护和扩展
        - 职责分离: 每个组件专注于特定的识别策略
        - 易于测试: 可以单独测试每个组件的功能
        """
        self.regex_parser = RegexIntentParser()  # 正则表达式意图解析器
        self.keyword_parser = KeywordIntentParser()  # 关键词权重意图解析器
        self.slot_extractor = SlotExtractor()  # 槽位信息提取器

    def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的意图识别流程

        Args:
            input_dict: 输入字典，必须包含 'text' 键

        Returns:
            Dict[str, Any]: 包含完整识别结果的字典

        返回字段说明:
        - intent: 识别的意图类型
        - confidence: 置信度分数 (0.0-1.0)
        - slots: 提取的槽位信息字典
        - matched_rules: 匹配的规则列表
        - extracted_entities: 提取的实体信息
        - reasoning: 推理过程的文字描述

        处理流程详解:
        1. 输入验证: 从输入字典中提取文本
        2. 并行解析: 同时运行正则和关键词解析器
        3. 结果融合: 根据策略选择最佳识别结果
        4. 槽位提取: 基于意图类型提取相关参数
        5. 推理生成: 生成可解释的推理过程
        6. 结果封装: 将所有信息整合为输出字典
        """
        # 步骤1: 提取输入文本，提供默认值避免KeyError
        text = input_dict.get("text", "")

        # 步骤2: 并行执行多个解析器
        # 注意: 这里是"并行"的概念，实际是顺序执行，但逻辑上独立
        regex_result = self.regex_parser.parse(text)  # 正则匹配解析
        keyword_result = self.keyword_parser.parse(text)  # 关键词匹配解析

        print(f"[Debug] Regex Result: {regex_result}")
        print(f"[Debug] Keyword Result: {keyword_result}")

        # 步骤3: 融合多个解析器的结果
        # 使用智能策略选择最佳结果
        final_result = self._merge_results([regex_result, keyword_result])

        print(f"[Debug] Final Merged Result: {final_result}")

        # 步骤4: 基于最终意图提取槽位信息
        slots = self.slot_extractor.extract_slots(text, final_result.intent)

        # 步骤5: 生成人类可读的推理解释
        reasoning = self._generate_reasoning(final_result)

        # 步骤6: 构造并返回完整的结果字典
        return {
            "intent": final_result.intent,  # 最终识别的意图
            "confidence": final_result.confidence,  # 置信度分数
            "slots": slots,  # 提取的槽位参数
            "matched_rules": final_result.matched_rules,  # 匹配的规则标识
            "extracted_entities": final_result.extracted_entities,  # 提取的实体
            "reasoning": reasoning  # 推理过程说明
        }

    def _merge_results(self, results: List[IntentResult]) -> IntentResult:
        """
        融合多个解析器的识别结果

        Args:
            results: 各个解析器返回的结果列表

        Returns:
            IntentResult: 融合后的最终识别结果

        融合策略说明:
        1. 优先级策略: 正则匹配 > 关键词匹配
        2. 置信度阈值: 正则匹配置信度 > 0.8 时直接采用
        3. 最优选择: 其他情况选择置信度最高的结果
        4. 兜底机制: 无有效结果时返回未知意图

        设计理念:
        - 正则匹配精确度高，优先级最高
        - 关键词匹配覆盖面广，作为补充
        - 置信度机制确保结果质量
        - 兜底策略保证系统稳定性
        """
        # 步骤1: 过滤掉未知意图的结果
        # 只保留有效的识别结果进行后续处理
        valid_results = [r for r in results if r.intent != "unknown"]

        # 步骤2: 如果没有有效结果，返回默认的未知意图
        if not valid_results:
            return IntentResult()

        # 步骤3: 正则匹配优先策略
        # 如果正则匹配的置信度足够高(>0.8)，直接采用
        regex_results = [r for r in valid_results
                         if any("regex" in rule for rule in r.matched_rules)]
        if regex_results and regex_results[0].confidence > 0.8:
            return regex_results[0]

        # 步骤4: 置信度最优策略
        # 选择所有有效结果中置信度最高的
        best_result = max(valid_results, key=lambda x: x.confidence)
        return best_result

    def _generate_reasoning(self, result: IntentResult) -> str:
        """
        生成人类可读的推理解释

        Args:
            result: 最终的识别结果

        Returns:
            str: 推理过程的文字描述

        功能说明:
        - 提供系统决策的透明度
        - 帮助用户理解识别过程
        - 便于系统调试和优化
        - 增强用户对系统的信任度

        解释内容包括:
        - 使用的识别方法(正则/关键词)
        - 识别的意图类型
        - 对应的置信度分数
        """
        # 处理未知意图的情况
        if result.intent == "unknown":
            return "未匹配到任何规则"

        # 判断使用的识别方法
        rule_type = ("正则匹配" if any("regex" in rule for rule in result.matched_rules)
                     else "关键词匹配")

        # 生成格式化的推理说明
        return f"通过{rule_type}识别为{result.intent}，置信度{result.confidence:.2f}"
