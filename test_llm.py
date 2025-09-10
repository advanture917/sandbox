from sandbox.llm import SandboxLLM
from sandbox.const import BackendType, SupportedLanguage
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取环境变量
api_key = os.environ.get("API_KEY")
base_url = os.environ.get('BASE_URL')
model_name = os.environ.get('MODEL_NAME')
# Test Python code generation and execution
print("=== Testing Python Code Generation and Execution ===")
llm_python = SandboxLLM(backend_type=BackendType.DOCKER, model_name=model_name,api_key=api_key,base_url=base_url, language=SupportedLanguage.PYTHON)

# Test task without dependencies
task1 = "Calculate the sum of numbers from 1 to 100 and print the result."
print("Running task 1: Calculate the sum of numbers from 1 to 100")
result1 = llm_python.run_code(task1)
print(f"Exit code: {result1.exit_code}")
print(f"Stdout: {result1.stdout}")
print(f"Stderr: {result1.stderr}")

# Test task that intentionally generates a SyntaxError
# This is used to test the LLM automatic code correction logic
task2 = """
编写 Python 代码生成前 20 个斐波那契数列的平方，并将它们按从大到小排序后打印。
请在代码中故意引入一个语法错误，例如在循环中缺少冒号。
"""
print("\nRunning task 2: Create a numpy array and calculate the mean")
result2 = llm_python.run_code(task2)
print(f"Exit code: {result2.exit_code}")
print(f"Stdout: {result2.stdout}")
print(f"Stderr: {result2.stderr}")
