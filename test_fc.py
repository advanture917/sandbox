
import openai
from sandbox.session import SandboxSession
from typing import Optional, List
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
def execute_code(
        code: str,
        language: str = "python",
        libraries: Optional[List[str]] = None
) -> str:
    """
    在安全的沙箱环境中执行代码

    参数:
        code: 要执行的代码字符串
        language: 代码语言，目前仅支持python
        libraries: 需要导入的库列表，如["numpy", "pandas"]

    返回:
        代码执行结果的标准输出，如果执行出错则返回错误信息
    """
    # 验证语言类型
    if language not in ["python"]:
        return f"错误: 不支持的语言 {language}，目前仅支持python"

    # 确保libraries是列表类型
    if libraries is not None and not isinstance(libraries, list):
        return "错误: libraries参数必须是字符串列表"

    try:
        with SandboxSession() as session:
            # 处理依赖库，移除空字符串并去重
            dependencies = None
            if libraries:
                dependencies = list(filter(None, set(libraries)))  # 去重和过滤空值

            result = session.run_code(code=code, dependencies=dependencies)
            print(f"{result}")
            return result
    except Exception as e:
        return f"执行过程中发生错误: {str(e)}"
## 步骤2:创建 tools 数组

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "在安全沙箱中执行代码，目前仅支持Python。可指定需要导入的库列表。",
            "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的代码字符串，必须是完整可运行的代码"
                },
                "language": {
                    "type": "string",
                    "enum": ["python"],
                    "description": "代码语言，默认为python"
                },
                "libraries": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "需要导入的库列表，例如[\"numpy\", \"pandas\"]"
                }
            },
            "required": ["code"]
            }
        }
    }
]
tool_name = [tool["function"]["name"] for tool in tools]

# 加载 .env 文件
load_dotenv()

# 读取环境变量
api_key = os.environ.get("API_KEY")
model_name = os.environ.get("MODEL_NAME")
base_url = os.environ.get("BASE_URL")

client = OpenAI(base_url = base_url, api_key=api_key)
user_query = """
计算1到100的总和，要求：
1. 编写Python代码实现计算逻辑；
2. 通过execute_code函数运行该代码；
3. 返回代码运行后的输出结果，不直接用公式计算。
"""
system_prompt = """
你拥有调用工具的能力，当需要执行代码时，必须使用以下格式调用 `execute_code` 函数，不允许直接输出代码结果或用自然语言解答：
"""
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}],
    tools=tools
)


# print("返回对象：")
# print(response.choices[0].message.model_dump_json())
# print("\n")
function_name = response.choices[0].message.tool_calls[0].function.name
arguments_string = response.choices[0].message.tool_calls[0].function.arguments
# 使用json模块解析参数字符串
arguments = json.loads(arguments_string)

print(f"✅{arguments}")
arguments["code"] = arguments["code"].encode("utf-8").decode("utf-8")
print(f"✅{arguments}")
# 创建一个函数映射表
function_mapper = {
    "execute_code": execute_code,
    # "get_current_time": get_current_time
}
# 获取函数实体
function = function_mapper[function_name]
# 如果入参为空，则直接调用函数
if arguments == {}:
    function_output = function()
# 否则，传入参数后调用函数
else:
    function_output = function(**arguments)
# 打印工具的输出
print(f"工具函数输出：{function_output}\n")

