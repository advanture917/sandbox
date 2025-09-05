import docker
from typing import Any
from pathlib import Path
import uuid
import base64
from sandbox.const import DefaultImage,SupportedLanguage
from sandbox.data import ExecutionRequest,ExeGenFileRequest
from sandbox.util import logger

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
    def _get_install_command(self,language:SupportedLanguage = SupportedLanguage.PYTHON ,libraries : list[str]=None)-> list[str]:
        match language:
            case SupportedLanguage.PYTHON:
                # pip install 直接接收列表元素作为参数
                return ["pip", "install", "--quiet"] + libraries

            case SupportedLanguage.GO:
                # go get 接收包名列表
                return ["go", "get"] + libraries
            case _:
                logger.error(f"不支持的语言: {language}")
                return []


    def _create_file(self,container:Any,code:str,language: SupportedLanguage= SupportedLanguage.PYTHON)-> str:
        file_path =""
        file_ext = {
            SupportedLanguage.PYTHON: ".py",
            SupportedLanguage.GO: ".go",
        }.get(language, ".txt")
        unique_id = uuid.uuid4().hex  # 生成32位随机字符串
        file_path = f"/sandbox/code_{unique_id}{file_ext}"
        # 对代码进行base64编码，避免所有特殊字符
        encoded_code = base64.b64encode(code.encode()).decode()

        # 在容器内解码并写入文件
        command = [
            "sh", "-c",
            f'echo "{encoded_code}" | base64 -d > {file_path}'
        ]
        container.exec_run(command)
        return file_path
    def _get_run_command(self,file_path :str,language:SupportedLanguage=SupportedLanguage.PYTHON)->list[str]:
        """生成代码执行命令"""
        match language:
            case SupportedLanguage.PYTHON:
                return ["python", file_path]
            case SupportedLanguage.GO:
                return ["go", "run", file_path]

    def run_code(self,container:Any , req:ExecutionRequest):
        """ run code in docker container."""
        code = req.code
        language = req.language
        libraries = req.dependencies
        # 处理包依赖
        if libraries is not  None:
            install_command = self._get_install_command(language = language,libraries=libraries)
            logger.info(f"install command is {install_command}")
            container.exec_run(cmd = install_command)
        file_path = self._create_file(container =container,code = code,language=language)
        # 将代码保存为对应的文件后执行
        # res = container.exec_run(["ls","/tmp/sandbox"])
        # logger.info(f"{res.output.decode('utf-8')}")
        command = self._get_run_command(file_path = file_path, language=language)
        result = container.exec_run(command)
        # return result.output.decode('utf-8')
        return  result

    def run_code_get_file(self, container: Any, req: ExeGenFileRequest):
        """
        run code in docker container and return generated files' content and stat
        """
        ret = self.run_code(
            container=container,
            req=ExecutionRequest(
                code=req.code,
                language=req.language,
                dependencies=req.dependencies
            )
        )
        logger.info(f"run output is {ret}")

        file_paths = req.file_path
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        if not isinstance(file_paths, list) or not file_paths:
            logger.warning("未提供有效的文件路径列表")
            return None, None

        files_content, files_stat = [], []
        for container_file_path in file_paths:
            try:
                if not container_file_path.startswith("/sandbox/"):
                    container_file_path = f"/sandbox/{container_file_path.lstrip('/')}"

                logger.info(f"🎉 开始复制文件{container_file_path}")
                res = container.exec_run(["pwd"])
                logger.info(f"当前工作目录: {res.output.decode()}")

                res = container.exec_run(["ls"])
                logger.info(f"当前目录内容{res.output.decode("utf-8")}")
                content, stat = self.copy_from_container(container, container_file_path)
                files_content.append(content)
                files_stat.append(stat)
            except Exception as e:
                logger.error(f"从容器复制文件失败: {container_file_path}, 错误: {e}")

        return files_content, files_stat

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
