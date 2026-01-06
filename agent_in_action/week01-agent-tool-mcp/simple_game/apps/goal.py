from dataclasses import dataclass


# Goal：目标对象
# - priority：目标优先级（便于排序/裁剪）
# - name/description：目标名称和详细说明（同时涵盖“要做什么/如何做”）
# 使用 @dataclass 装饰器定义 Goal 为一个不可变的数据类（frozen=True），这意味着其实例一旦创建，其属性值就不能被修改，有助于保证数据安全和可靠性。
@dataclass(frozen=True)
class Goal:
    priority: int
    name: str
    description: str
