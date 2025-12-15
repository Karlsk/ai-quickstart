import re
from typing import Dict


class SlotExtractor:
    """
    槽位信息提取器
    ==============

    功能说明:
    - 根据已识别的意图类型，提取执行该意图所需的参数信息
    - 使用正则表达式从用户输入中抽取结构化数据
    - 支持多种数据类型的提取(订单号、时间、金额等)

    槽位设计原则:
    - 每个意图类型对应一组特定的槽位
    - 槽位名称语义化，便于后续业务逻辑使用
    - 正则模式兼顾准确性和覆盖面

    应用场景:
    - 订单查询: 需要订单号、时间等参数
    - 退款申请: 需要订单号、退款原因、时间等
    - 开具发票: 需要订单号、金额等参数
    """

    def __init__(self):
        """
        初始化槽位提取模式配置

        配置结构说明:
        - 外层key: 意图类型 (如 'query_order')
        - 内层key: 槽位名称 (如 'order_id')
        - 内层value: 正则表达式模式 (用于提取对应信息)

        正则模式设计要点:
        - 使用捕获组 () 提取目标信息
        - 考虑中文表达的多样性
        - 平衡精确度和召回率
        """
        self.slot_patterns = {
            # 查询订单意图的槽位配置
            'query_order': {
                'order_id': r'(\d{6,})',  # 提取6位以上数字作为订单号
                'time': r'(昨天|今天|前天|上周|本月)'  # 提取时间表达
            },
            # 退款意图的槽位配置
            'refund': {
                'order_id': r'订单.*?(\d{6,})',  # 在"订单"关键词后提取数字
                'reason': r'因为(.*?)所以',  # 提取"因为...所以"中的原因
                'time': r'(昨天|今天|前天).*下.*单'  # 提取下单时间表达
            },
            # 开发票意图的槽位配置
            'issue_invoice': {
                'order_id': r'(\d{6,})',  # 提取订单号
                'amount': r'(\d+\.?\d*)元'  # 提取金额数字(支持小数)
            }
        }

    def extract_slots(self, text: str, intent: str) -> Dict[str, str]:
        """
        根据意图类型提取槽位信息

        Args:
            text: 用户输入的原始文本
            intent: 已识别的意图类型

        Returns:
            Dict[str, str]: 槽位名称到提取值的映射字典

        提取流程:
        1. 检查意图类型是否在配置中存在
        2. 遍历该意图对应的所有槽位模式
        3. 对每个槽位执行正则匹配
        4. 将匹配成功的结果保存到字典中
        5. 返回包含所有提取信息的槽位字典

        注意事项:
        - 如果意图类型不存在，返回空字典
        - 如果某个槽位匹配失败，该槽位不会出现在结果中
        - 只提取正则捕获组中的内容 (match.group(1))
        """
        slots = {}  # 初始化槽位结果字典

        # 检查当前意图是否有对应的槽位配置
        if intent in self.slot_patterns:
            patterns = self.slot_patterns[intent]  # 获取该意图的槽位模式

            # 遍历所有槽位，尝试提取信息
            for slot_name, pattern in patterns.items():
                # 执行正则匹配
                match = re.search(pattern, text)
                if match:
                    # 匹配成功，提取捕获组的内容
                    slots[slot_name] = match.group(1)
                    # 注意: match.group(1) 获取第一个捕获组的内容
                    # 如果需要多个捕获组，可以使用 match.groups()

        return slots  # 返回提取到的槽位信息字典
