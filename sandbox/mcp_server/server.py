from fastmcp import FastMCP
from sandbox.util import logger
from sandbox.errors import BackendError
from sandbox.session import SandboxSession
from sandbox.const import SupportedLanguage
from typing import List, Optional
import sandbox.errors
# test
# npx @modelcontextprotocol/inspector python -m sandbox.mcp_server.server
mcp = FastMCP("LLM-Sandbox")
@mcp.tool
def run_code_in_sandbox(
        code: str,
        language: str = "PYTHON",
        libraries: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
):
    """
    在受限的沙箱环境中运行用户代码，并返回执行结果。

    参数:
        code (str): 需要执行的代码字符串，例如:
            "print('Hello World')"
        language (str, 可选): 指定运行语言，默认为 "python"。
            可选值见 SupportedLanguage (如 "python", "cpp", "java")。
        libraries (List[str], 可选): 代码执行所需的依赖库列表，例如 ["numpy", "pandas"]。
            若为空，则不安装额外依赖。
        file_paths (List[str], 可选): 运行过程中需要生成或读取的文件路径。
            - 如果代码写入文件，则传入文件路径数组（如 ["test1.txt"]）
            - 沙箱执行后会自动将这些文件保存到宿主机可访问目录，并返回路径。
    """
    import time
    try:
        # 进入沙箱上下文
        with SandboxSession(language=SupportedLanguage[language]) as sb:
            # 执行代码
            result = sb.run_code(
                code=code,
                dependencies=libraries or [],
                # file_path="test1.txt"
            )
        return result
        # file_paths = "test1.txt"
    except Exception as e:
        raise BackendError(f"backend error {e}")
    logger.info(f"{result}")
    # # mcp
    # res = {
    #     "res" :result if file_paths is None else f"Generated {result}",
    # }
    return result

if __name__ == "__main__":
    mcp.run(transport= "stdio")