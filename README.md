# Sandbox

一个支持多语言和多种容器方式（如Docker/K8s）的代码执行沙箱。

## 特性

- 支持多种编程语言（Python, Go）
- 支持多种容器方式（Docker, Kubernetes）
- 使用工厂模式管理不同的后端实现
- 易于扩展以支持更多语言和容器方式

## 安装

```bash
pip install -r requirements.txt
```

## 使用示例

### Docker后端

```python
from sandbox.session import SandboxSession
from sandbox.const import BackendType, SupportedLanguage

with SandboxSession(backend=BackendType.DOCKER, language=SupportedLanguage.PYTHON) as session:
    code = "print('Hello, Docker!')"
    result = session.run_code(code)
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")
```

### Kubernetes后端

```python
from sandbox.session import SandboxSession
from sandbox.const import BackendType, SupportedLanguage

with SandboxSession(backend=BackendType.KUBERNETES, language=SupportedLanguage.PYTHON) as session:
    code = "print('Hello, Kubernetes!')"
    result = session.run_code(code)
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")
```


## 使用SandboxLLM

SandboxLLM 是一个基于 Langchain 的 LLM，可以生成代码并在沙箱中执行。如果代码执行失败或输出不符合预期，它会自动重试并修复代码。

```python
from sandbox.llm import SandboxLLM
from sandbox.const import BackendType, SupportedLanguage
import os

# Initialize the SandboxLLM for Python
llm_python = SandboxLLM(
    backend_type=BackendType.DOCKER, 
    model_name=os.environ.get('MODEL_NAME', 'Qwen/Qwen3-30B-A3B-Thinking-2507'),
    base_url=os.environ.get('BASE_URL', ''),
    api_key=os.environ.get('API_KEY', ''),
    language=SupportedLanguage.PYTHON
)


# Run a task with dependencies 
task = "Create a numpy array with values from 1 to 10, calculate the mean and print it."
result = llm_python.run_code(task)
print(f"Exit code: {result.exit_code}")
print(f"Output: {result.stdout}")

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


```

### LLM 功能特性

- **自动代码生成**：根据自然语言任务描述生成相应语言的代码
- **依赖管理**：自动识别并安装代码所需的依赖库
- **错误修复**：当代码执行失败时，自动分析错误并修复代码
- **输出验证**：可选的输出验证功能，确保执行结果符合预期
