"""
企业级 LangChain 应用 - 智能客服系统
兼容当前版本，包含完整的错误处理和容错机制
"""

from utils import logger
from service import EnterpriseCustomerService

def demo_enterprise_application():
    """企业应用演示"""
    print("=== 企业级 LangChain 客服系统演示 ===")

    # 初始化系统
    customer_service = EnterpriseCustomerService()

    # 测试用例
    test_cases = [
        {
            "question": "我的API调用出现500错误，怎么解决？",
            "user_info": {"user_id": "12345", "plan": "企业版", "region": "北京"}
        },
        {
            "question": "我想查看本月的账单详情",
            "user_info": {"user_id": "67890", "plan": "标准版", "region": "上海"}
        },
        {
            "question": "你们的服务怎么样？",
            "user_info": {"user_id": "11111", "plan": "免费版", "region": "深圳"}
        }
    ]

    # 单个处理演示
    print("\n--- 单个处理演示 ---")
    for i, case in enumerate(test_cases, 1):
        print(f"\n客户咨询 {i}:")
        print(f"问题: {case['question']}")
        print(f"用户信息: {case['user_info']}")

        result = customer_service.process_customer_inquiry(
            case["question"],
            case["user_info"]
        )

        print(f"回复: {result['response']}")
        print(f"类别: {result['category']}")
        print(f"置信度: {result['confidence']}")
        print(f"需要人工: {result['requires_human']}")
        print(f"处理时间: {result['processing_time']}秒")
        print(f"状态: {result['status']}")

    # 批量处理演示
    print(f"\n--- 批量处理演示 ---")
    batch_results = customer_service.batch_process_inquiries(test_cases)

    print(f"批量处理了 {len(batch_results)} 个咨询")
    for i, result in enumerate(batch_results, 1):
        print(f"结果 {i}: {result['category']} - {result['response']}...")

    # 性能统计
    print(f"\n--- 性能统计 ---")
    stats = customer_service.get_performance_stats()
    print(f"总请求数: {stats['total_requests']}")
    print(f"成功请求数: {stats['successful_requests']}")
    print(f"失败请求数: {stats['failed_requests']}")
    print(f"成功率: {stats['success_rate']}%")
    print(f"平均响应时间: {stats['average_response_time']}秒")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    demo_enterprise_application()