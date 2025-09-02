# data.py
from enum import StrEnum
import json
import warnings
from dataclasses import dataclass, field
from sandbox.const import SupportedLanguage
class FileType(StrEnum):
    # 定义返回的文件类型
    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"
    SVG = "svg"
    CSV = "csv"
    JSON = "json"
    TXT = "txt"
    HTML = "html"


@dataclass(frozen=True)
class PlotOutput:
    """
    定义绘图代码的返回
    format: FileType 返回的图表类型 : PNG JPEG SVG等
    img_base64: str encode img by base64
    width: int | None = None
    height: int | None = None
    """

    format: FileType
    img_base64: str
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class ConsoleOutput:
    r"""Represents the standard output and standard error from code execution or a command.

    Attributes:
        exit_code (int): The exit code of the executed code or command. 0 typically indicates success.
        stderr (str): The content written to the standard error stream.
        stdout (str): The content written to the standard output stream.

    """

    exit_code: int = 0
    stderr: str = ""
    stdout: str = ""

    def text(self) -> str:
        r"""Get the text representation of the console output (stdout).

        .. deprecated:: 0.1.0
            The `text` property is deprecated and will be removed in a future version.
            Use the `stdout` attribute directly instead.

        Returns:
            str: The content of the standard output stream.

        """
        warnings.warn(
            "The 'text' property is deprecated and will be removed in a future version. "
            "Use 'stdout' attribute directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.stdout

    def success(self) -> bool:
        r"""Check if the execution was successful (exit code is 0).

        Returns:
            bool: True if `exit_code` is 0, False otherwise.

        """
        return not self.exit_code

    def to_json(self, include_plots: bool = False) -> str:
        r"""Get the JSON representation of the execution result.

        Args:
            include_plots (bool): Whether to include the plots in the JSON representation.

        Returns:
            str: The JSON representation of the execution result.

        """
        result = self.__dict__.copy()
        if not include_plots and "plots" in result:
            result.pop("plots", None)

        return json.dumps(result, indent=2)

@dataclass
class ExecutionRequest:
    code: str
    language: SupportedLanguage =SupportedLanguage.PYTHON
    dependencies: list[str] | None = None
    # timeout: int = 30

@dataclass(frozen=True)
class ExecutionResult(ConsoleOutput):
    r"""Represents the comprehensive result of code execution within a sandbox session.

    This class extends `ConsoleOutput` to include any plots or other file artifacts
    that were generated and captured during the execution.

    Attributes:
        plots (list[PlotOutput]): A list of `PlotOutput` objects, each representing a
                                    captured plot or visual artifact. Defaults to an empty list.

    """

    plots: list[PlotOutput] = field(default_factory=list)
