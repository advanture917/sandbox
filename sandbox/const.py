# const.py
from enum import StrEnum
class BackendType(StrEnum):
    """支持的沙箱后端技术常量集合"""
    DOCKER = "docker"
    # TODO 支持更多类型
    KUBERNETES = "kubernetes"

    @classmethod
    def _missing_(cls, value: object) -> "BackendType":
        if isinstance(value, str):
            print(cls)
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return super()._missing_(value)
class SupportedLanguage(StrEnum):
    r"""Dataclass defining constants for supported programming languages.

    Each attribute represents a language identifier string used by the sandbox
    to select appropriate language handlers and container images.
    """

    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    CPP = "cpp"
    GO = "go"
    RUBY = "ruby"
    R = "r"

class DefaultImage(StrEnum):
    """当前的默认镜像"""
    # TODO 添加更多语言
    PYTHON = "my-sandbox"
    GO = ""