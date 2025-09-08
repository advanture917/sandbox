# Sandbox

一个支持多语言和多种容器方式（如Docker/K8s）的代码执行沙箱。

## 特性

- 支持多种编程语言（Python, Go, Java, JavaScript, C++, Ruby, R等）
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

## 扩展

### 添加新的语言支持

1. 在`sandbox/const.py`中的`SupportedLanguage`枚举中添加新的语言
2. 在`sandbox/const.py`中的`DefaultImage`枚举中为新语言添加默认镜像
3. 在`sandbox/backend/docker.py`和`sandbox/backend/k8s.py`中更新语言到镜像的映射关系
4. 在`sandbox/backend/docker.py`中实现新语言的依赖处理和代码执行命令

### 添加新的容器方式

1. 创建新的后端实现类，继承自`sandbox/backend/base.py`中的`Backend`类
2. 在`sandbox/backend/__init__.py`中注册新的后端实现
3. 在`sandbox/const.py`中的`BackendType`枚举中添加新的容器方式
4. 在`sandbox/session.py`中添加新容器方式的处理逻辑