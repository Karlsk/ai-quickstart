from .models import IntentResult


class KeywordIntentParser:
    """
    关键词权重意图解析器
    ==================

    功能说明:
    - 基于关键词权重打分机制进行意图识别
    - 支持主关键词和次关键词的分层权重设计
    - 通过累积得分确定最终意图
    - 提供中等置信度的识别结果

    设计思路:
    - 主关键词: 强相关词汇，权重较高(0.8)
    - 次关键词: 弱相关词汇，权重较低(0.4)
    - 总分计算: 各匹配词汇权重之和，最大值截断为1.0

    适用场景:
    - 自然语言表达的意图识别
    - 模糊匹配和语义相关性判断
    - 正则匹配失败时的备选方案
    """

    def __init__(self):
        """
        初始化关键词权重配置

        配置结构说明:
        - primary: 主关键词列表，直接表达意图的核心词汇
        - secondary: 次关键词列表，间接相关的辅助词汇
        - weights: 权重配置，定义不同级别关键词的得分

        权重设计原则:
        - 主关键词权重(0.8): 单个词就能较强表达意图
        - 次关键词权重(0.4): 需要多个词组合才能确定意图
        - 总分上限(1.0): 避免过度累积导致的置信度失真
        """
        self.keywords = {
            # 查询订单意图的关键词配置
            'query_order': {
                'primary': ['查订单', '订单状态', '物流信息'],  # 直接表达查询意图
                'secondary': ['快递', '发货', '到了吗'],  # 间接相关的查询词汇
                'weights': {'primary': 0.8, 'secondary': 0.4}
            },
            # 退款意图的关键词配置
            'refund': {
                'primary': ['退钱', '退款', '退货'],  # 直接表达退款意图
                'secondary': ['不要', '取消', '退回'],  # 间接表达不满意的词汇
                'weights': {'primary': 0.8, 'secondary': 0.4}
            },
            # 开发票意图的关键词配置
            'issue_invoice': {
                'primary': ['开发票', '要发票', '发票'],  # 直接表达开票意图
                'secondary': ['报销', '开票'],  # 相关的财务词汇
                'weights': {'primary': 0.8, 'secondary': 0.4}
            }
        }

    def parse(self, text: str) -> IntentResult:
        """
        基于关键词权重解析意图

        Args:
            text: 用户输入的文本

        Returns:
            IntentResult: 包含意图、置信度、匹配词汇等信息的结果对象

        算法流程:
            1. 遍历所有意图类型
            2. 对每个意图计算关键词匹配得分
            3. 累积主关键词和次关键词的权重得分
            4. 选择得分最高的意图作为最终结果
            5. 如果没有任何匹配，返回未知意图
            """
        scores = {}  # 存储每个意图的得分信息

        # 遍历所有意图类型及其关键词配置
        for intent, config in self.keywords.items():
            score = 0  # 当前意图的累积得分
            matched_words = []  # 匹配到的关键词列表

            # 计算主关键词得分
            for word in config['primary']:
                if word in text:  # 简单的字符串包含匹配
                    score += config['weights']['primary']  # 累加主关键词权重
                    matched_words.append(word)  # 记录匹配的词汇

            # 计算次关键词得分
            for word in config['secondary']:
                if word in text:  # 简单的字符串包含匹配
                    score += config['weights']['secondary']  # 累加次关键词权重
                    matched_words.append(word)  # 记录匹配的词汇

            # 如果有匹配的关键词，记录该意图的得分信息
            if score > 0:
                scores[intent] = {
                    'score': min(score, 1.0),  # 得分上限截断为1.0
                    'matched_words': matched_words  # 保存匹配的词汇列表
                }

        # 如果有得分的意图，选择得分最高的作为结果
        if scores:
            # 找到得分最高的意图
            best_intent = max(scores.keys(), key=lambda x: scores[x]['score'])
            return IntentResult(
                intent=best_intent,  # 最佳意图
                confidence=scores[best_intent]['score'],  # 对应的置信度得分
                matched_rules=[f"keyword_{best_intent}"],  # 匹配规则标识
                extracted_entities=tuple(scores[best_intent]['matched_words'])  # 匹配的关键词
            )

        # 没有任何关键词匹配，返回默认的未知意图结果
        return IntentResult()

