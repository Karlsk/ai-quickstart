# 临时修复脚本 - 用于替换有问题的部分

FIX_CODE = '''        # 关键：使用 ConfigDict 允许任意字段添加（Dify 风格）
        from pydantic import ConfigDict
        
        # 创建有 ConfigDict 的基类
        class DynamicStateBase(BaseModel):
            model_config = ConfigDict(extra='allow')
        
        # 动态创建模型，继承自定义基类
        DynamicState = create_model(
            'DynamicWorkflowState',
            **field_definitions,
            __base__=DynamicStateBase
        )
        
        return DynamicState'''

# 读取文件
with open('graph_builder.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换（从第一个 # 关键 开始到 return DynamicState）
import re
pattern = r'(        # 关键：使用 ConfigDict 允许.*?\n        )(.*?\n        return DynamicState)'
content = re.sub(pattern, FIX_CODE, content, flags=re.DOTALL)

# 写回
with open('graph_builder.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 修复完成")
