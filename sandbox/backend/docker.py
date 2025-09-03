import docker
from typing import Any
from pathlib import Path
from sandbox.const import DefaultImage,SupportedLanguage
from sandbox.data import ExecutionRequest
# 实现Docker容器子类

class DockerBackend:
    def __init__(
            self,
            client:docker.DockerClient,
            stream : bool = False
            # default_lifecycle: ContainerLifePolicy = ContainerLifePolicy.ON_COMPLETION_REMOVE,
            # max_execution_time: int = 600  # 最大运行时间（秒），默认10分钟
    ):
        # client = docker.from_env()
        self.client = client
        self.stream = stream
        # 语言到镜像的映射关系
        self.lang_to_image = {
            SupportedLanguage.PYTHON: DefaultImage.PYTHON,
            # 待添加
            SupportedLanguage.GO:DefaultImage.GO

        }
    # 对于container 的增删改查
    def create_container(self, lang: str,  **kwargs):
        """
        根据语言创建对应的容器

        :param lang: 编程语言名称（如"python"、"java"）
        :param lifecycle : 容器生命管理策略
        :param kwargs: 传递给docker client的其他参数（如command、ports等）
        :return: 创建的容器对象
        """
        # 转换为小写统一处理
        lang_lower = lang.lower()

        # 检查是否支持该语言
        if lang_lower not in self.lang_to_image:
            raise ValueError(f"不支持的语言: {lang}，支持的语言有: {list(self.lang_to_image.keys())}")

        # 获取对应的镜像
        image = self.lang_to_image[lang_lower]

        # 创建并返回容器
        container = self.client.containers.create(
            image=image,
            command="tail -f /dev/null",
            **kwargs
        )
        # 后续考虑添加容器管理
        # with self._container_lock:
        #     self.managed_containers.append({
        #         "container": container,
        #         "lifecycle": lifecycle,
        #         "start_time": time.time(),
        #         "id":container.id
        #     })
        return container
    def start_container(self, container: Any) -> None:
        """Start Docker container."""
        container.start()

    def stop_container(self, container: Any) -> None:
        """Stop Docker container."""
        container.stop()

    def execute_command(self, container: Any, command: str, **kwargs: Any) -> tuple[int, Any]:
        """Execute command in Docker container."""
        workdir = kwargs.get("workdir")
        exec_kwargs: dict[str, Any] = {
            "cmd": command,
            "stream": self.stream,
            "tty": False,
            "stderr": True,
            "stdout": True,
            "demux": True,
        }
        if workdir:
            exec_kwargs["workdir"] = workdir

        result = container.exec_run(cmd = command)
        # print(f"✅✅{result}")
        return result.exit_code or 0, result.output
    def run_code(self,container:Any , req:ExecutionRequest):
        code = req.code
        language = req.language
        libraries = req.dependencies
        install_code = ""
        # 对command 添加 安装依赖库
        match language:
            case SupportedLanguage.PYTHON:
                install_code = f"""
import subprocess
import sys
import os

# 安装用户指定的依赖库（静默模式）
libraries = {libraries}
if libraries is not None:
    for lib in libraries:
    # 使用--quiet参数减少输出，并重定向stdout和stderr
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", lib],
            stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT
        )
# 执行用户提供的代码
{code}
                """
            case SupportedLanguage.GO:
                pass

        command = ["python", "-c", install_code]
        print(f"{install_code}")
        result = container.exec_run(command)
        return result.output.decode('utf-8')

    def remove_container (self,container :Any):
        return container.remove(v = True)


    def copy_to_container(self, container: Any, src: str, dest: str, **_kwargs: Any) -> None:
        """Copy file to Docker container."""
        import io
        import tarfile

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(src, arcname=Path(dest).name)

        tar_stream.seek(0)
        container.put_archive(Path(dest).parent.as_posix(), tar_stream.getvalue())

    def copy_from_container(self, container: Any, src: str, **_kwargs: Any) -> tuple[bytes, dict]:
        """Copy file from Docker container."""
        data, stat = container.get_archive(src)
        return b"".join(data), stat

