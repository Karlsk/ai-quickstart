import os

from apps.action import Action, ActionRegistry
from apps.environment import Environment
from apps.agent_language import AgentFunctionCallingActionLanguage
from apps.agent import Agent
from apps.goal import Goal
from apps.memory import Memory

from pathlib import Path
from typing import List



# =============================== 示例：最小可运行 Agent ===============================
# 1) 定义智能体目标（Goals）：
#    - 读取项目中的每个文件
#    - 当已读取完毕时调用 terminate，并在消息中提供 README 的内容（示例环境如为空目录会直接终止）
goals = [
    Goal(
        priority=1,
        name="Gather Information",
        description="Read each file in the project",
    ),
    Goal(
        priority=2,
        name="Terminate When Done",
        description="Call the terminate call when you have read all the files "
                    "and provide the content of the README in the terminate message",
    ),
]

# 2) 指定语言适配器（基于函数调用的 Prompt/解析策略）
agent_language = AgentFunctionCallingActionLanguage()


# 3) 实现底层动作：读取文件
def read_project_file(name: str) -> str:
    with open(name, "r") as f:
        return f.read()


# 4) 实现底层动作：列出当前目录及子目录下的 .py 文件（最小示例）
def list_project_files() -> List[str]:
    """
    使用 pathlib.Path.rglob 递归查找所有 .py 文件。
    """
    # 1. Path(".") 代表当前目录
    # 2. .rglob("*.py") 递归地 (r) 查找 (glob) 所有匹配 "*.py" 的文件

    # rglob 会返回一个生成器，包含所有匹配的 Path 对象
    py_files_paths = Path("/Users/gaorj/PycharmProjects/Learning/ai-quickstart/agent_in_action/week01/mcp_demo").rglob("*.py")

    # 3. 将 Path 对象转换为字符串，并确保它们是文件（排除目录）
    #    str(p) 会自动生成正确的相对路径（例如 'my_app/helpers.py'）
    files = [str(p) for p in py_files_paths if p.is_file()]

    return sorted(files)


# 5) 注册动作：将 Python 函数“暴露”为可被 LLM 选择的工具
action_registry = ActionRegistry()
action_registry.register(Action(
    name="list_project_files",
    function=list_project_files,
    description="Lists all files in the project.",
    parameters={},
    terminal=False
))
action_registry.register(Action(
    name="read_project_file",
    function=read_project_file,
    description="Reads a file from the project.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    },
    terminal=False
))
action_registry.register(Action(
    name="terminate",
    function=lambda message: f"{message}\nTerminating...",
    description="Terminates the session and prints the message to the user.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string"}
        },
        "required": []
    },
    terminal=True
))

# 6) 准备环境（负责真实执行动作并返回标准化结果）
environment = Environment()

if __name__ == "__main__":
    # 7) 构建 Agent 实例（组装 G/A/M/E 与 LLM 响应函数）
    from apps.llm import generate_response
    agent = Agent(goals, agent_language, action_registry, generate_response, environment)

    # 8) 运行智能体（输入一个自然语言任务），内部会进入循环直到触发终止或达到最大轮数
    user_input = "Write a README for this project."
    final_memory = agent.run(user_input)

    # 9) 输出最终的记忆（包含用户任务、助手决策、环境执行结果等）
    print(final_memory.get_memories())

    # 将智能体运行结果以 Markdown 形式美化展示
    from IPython.display import display, Markdown
    import json


    def _format_env_result(env_json_str: str) -> str:
        try:
            obj = json.loads(env_json_str)
        except Exception:
            return env_json_str
        if isinstance(obj, dict) and obj.get("tool_executed") is True:
            result = obj.get("result", "")
            ts = obj.get("timestamp", "")
            if isinstance(result, list):
                body = "\n".join([f"- {x}" for x in result])
                return f"执行成功（{ts}）\n\n可用文件列表：\n{body}"
            if isinstance(result, str):
                if result.strip().startswith("# ") or "\n## " in result:
                    return f"执行成功（{ts}）\n\n生成内容：\n\n```markdown\n{result}\n```"
                return f"执行成功（{ts}）\n\n```text\n{result}\n```"
            return f"执行成功（{ts}）\n\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
        if isinstance(obj, dict) and obj.get("tool_executed") is False:
            err = obj.get("error", "")
            tb = obj.get("traceback", "")
            return f"执行失败\n\n错误：`{err}`\n\n<details><summary>Traceback</summary>\n\n```text\n{tb}\n```\n\n</details>"
        return f"```json\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n```"


    md_lines = [
        "# 智能体执行报告",
    ]

    if 'final_memory' not in globals():
        display(Markdown("> 未检测到 final_memory 变量，请先运行上方示例执行智能体。"))
    else:
        memories = final_memory.get_memories()

        # 概览
        md_lines.append("## 概览")
        md_lines.append(f"- 总事件数：{len(memories)}")

        # 逐步展示
        md_lines.append("\n## 交互明细\n")
        for idx, item in enumerate(memories, 1):
            typ = item.get("type", "unknown")
            content = item.get("content", "")
            if typ == "user":
                md_lines.append(f"### 步骤 {idx} · 用户输入")
                md_lines.append(f"> {content}")
            elif typ == "assistant":
                md_lines.append(f"### 步骤 {idx} · 助手决策（工具调用）")
                try:
                    call = json.loads(content)
                    tool = call.get("tool", "?")
                    args = call.get("args", {})
                    md_lines.append(f"- 工具：`{tool}`")
                    md_lines.append("- 参数：")
                    md_lines.append(f"```json\n{json.dumps(args, ensure_ascii=False, indent=2)}\n```")
                except Exception:
                    md_lines.append("- 文本回复：")
                    md_lines.append(f"```text\n{content}\n```")
            elif typ == "environment":
                md_lines.append(f"### 步骤 {idx} · 环境执行结果")
                md_lines.append(_format_env_result(content))
            else:
                md_lines.append(f"### 步骤 {idx} · 其他")
                md_lines.append(f"```text\n{content}\n```")

        # 摘取 README 内容（若存在 terminate 消息）
        md_lines.append("\n## 生成的 README（若已终止并返回）\n")
        readme_blocks = []
        for item in memories[::-1]:
            if item.get("type") == "environment":
                try:
                    obj = json.loads(item["content"]) if isinstance(item.get("content"), str) else item["content"]
                    if obj.get("tool_executed") and isinstance(obj.get("result"), str) and obj[
                        "result"].lstrip().startswith("# "):
                        readme_blocks.append(obj["result"].replace("\nTerminating...", "").strip())
                        break
                except Exception:
                    pass
        if readme_blocks:
            md_lines.append("```markdown\n" + readme_blocks[0] + "\n```")
        else:
            md_lines.append("> 本次执行未生成 README 内容或未调用终止工具。")

        display(Markdown("\n\n".join(md_lines)))
