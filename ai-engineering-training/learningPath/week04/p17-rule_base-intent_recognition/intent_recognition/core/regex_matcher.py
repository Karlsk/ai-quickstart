import re

from .models import IntentResult
class RegexIntentParser:
    """
    正则表达式意图解析器
    ==================

    功能说明:
    - 使用预定义的正则表达式模式匹配用户输入
    - 支持多种意图类型的精确匹配
    - 能够提取结构化信息(如订单号、数字等)
    - 具有最高的匹配优先级(置信度0.9)

    适用场景:
    - 结构化表达的识别 (如"订单号123456")
    - 固定格式的用户输入
    - 需要提取特定信息的场景
    """

    def __init__(self):
        """
        初始化正则模式字典

        模式设计原则:
        1. 使用 .* 匹配任意字符，增加灵活性
        2. 使用 (\d+) 捕获数字信息
        3. 使用 .*? 进行非贪婪匹配
        4. 按匹配精确度排序，精确的模式放在前面
        """
        self.patterns = {
            # 查询订单相关模式
            'query_order': [
                r'查.*订单.*(\d+)',  # 匹配: "查订单123" -> 提取数字
                r'订单号.*?(\d{6,})',  # 匹配: "订单号123456" -> 提取6位以上数字
                r'我的订单.*状态'  # 匹配: "我的订单状态" -> 无提取
            ],
            # 退款相关模式
            'refund': [
                r'退.*款',  # 匹配: "退款"、"申请退款"
                r'取消.*订单',  # 匹配: "取消订单"、"取消这个订单"
                r'不要.*了'  # 匹配: "不要了"、"我不要这个了"
            ],
            # 开发票相关模式
            'issue_invoice': [
                r'开.*发票',  # 匹配: "开发票"、"帮我开个发票"
                r'要.*发票',  # 匹配: "要发票"、"我要发票"
                r'发票.*开'  # 匹配: "发票怎么开"
            ]
        }

    def parse(self, text: str) -> IntentResult:
        """
        解析文本并返回意图结果

        Args:
            text: 用户输入的文本

        Returns:
            IntentResult: 包含意图、置信度、匹配规则等信息的结果对象

        处理流程:
            1. 遍历所有意图类型
            2. 对每个意图的所有模式进行匹配
            3. 找到第一个匹配的模式就立即返回(优先级机制)
            4. 如果没有匹配，返回默认的未知意图结果
        """
        # 遍历所有意图类型和对应的正则模式
        for intent, patterns in self.patterns.items():
            # 遍历当前意图的所有正则模式
            for i, pattern in enumerate(patterns):
                # 执行正则匹配，忽略大小写
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # 匹配成功，构造并返回结果
                    return IntentResult(
                        intent=intent,  # 意图类型
                        confidence=0.9,  # 正则匹配的高置信度
                        matched_rules=[f"regex_{intent}_{i}"],  # 匹配规则标识
                        extracted_entities=match.groups() if match.groups() else None  # 提取的实体
                    )

        # 没有任何模式匹配，返回默认结果
        return IntentResult()

