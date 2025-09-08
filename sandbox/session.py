import docker
import os
from sandbox.const import BackendType,SupportedLanguage
from sandbox.backend.base import Backend, BackendFactory
from sandbox.backend.docker import DockerBackend
from sandbox.backend.k8s import K8sBackend
from sandbox.errors import  BackendError,BackendNotAvailable
from sandbox.util import logger
from sandbox.data import ExecutionRequest, ExeGenFileRequest
from typing import Any
import io, tarfile

class SandboxSession:
    def __init__(
            self,
            backend_type:BackendType = BackendType.DOCKER,
            language:SupportedLanguage = SupportedLanguage.PYTHON):
        self.backend_type = backend_type
        self.language = language
        self.backend = None
        self.container = None

    def __enter__(self):
        """进入上下文时启动 backend"""
        # 使用工厂模式创建后端实例
        if self.backend_type in BackendFactory.get_available_backends():
            if self.backend_type == BackendType.DOCKER:
                client = docker.from_env()
                self.backend = BackendFactory.create_backend(self.backend_type, client=client)
            elif self.backend_type == BackendType.KUBERNETES:
                self.backend = BackendFactory.create_backend(self.backend_type)
        else:
            raise BackendNotAvailable(f"Backend {self.backend_type} not implemented")

        logger.info(f"Creating container for language={self.language} and backend = {self.backend_type}")
        self.container = self.backend.create_container(lang=self.language)

        logger.info("Starting container...")
        self.backend.start_container(self.container)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时释放资源"""
        if self.backend and self.container:
            try:
                logger.info("Stopping container...")
                self.backend.stop_container(self.container)
            except Exception as e:
                logger.error(f"Failed to stop container: {e}")
            finally:
                try:
                    logger.info("Removing container...")
                    self.backend.remove_container(self.container)
                except Exception as e:
                    logger.error(f"Failed to remove container: {e}")

    def exe_command(self,command:str,**kwargs:Any) -> 'CommandResult':
        return self.backend.execute_command(self.container,command,**kwargs)

    def run_code(self, code: str, dependencies: list[str] | None = None, file_path: list[str] | str = None):
        """
        执行代码，支持普通执行和生成文件两种模式

        Args:
            code: 要执行的代码
            dependencies: 依赖列表
            file_path: 当需要生成文件时，指定文件路径列表，为None时执行普通模式
        """
        if file_path is not None:
            # 生成文件模式
            request = ExeGenFileRequest(
                code=code,
                language=self.language,
                dependencies=dependencies,
                file_path=file_path,
            )
            files_content , files_stat  = self.backend.run_code_get_file(self.container, request)
            logger.info(f"Return code: {files_stat}")
            return self._creat_local_file(files_content,files_stat)
        else:
            # 普通执行模式
            request = ExecutionRequest(
                code=code,
                language=self.language,
                dependencies=dependencies,
            )
            return self.backend.run_code(self.container, request)

    def _creat_local_file(self,files_content:list[bytes] | None = None,files_stat:list[dict] | None = None)-> list[str] | None:
        """
            将从容器中获取的文件内容保存到本地
            Args:
                files_content: 文件的二进制内容列表
                files_stat: 每个文件的元信息
            Returns:
                保存到本地的文件路径列表
            """
        local_output = "./output"
        os.makedirs(local_output, exist_ok=True)
        logger.info(f"文件将保存到本地目录: {local_output}")

        if not files_content or not files_stat:
            logger.warning("没有提供文件内容或文件元信息，跳过保存")
            return None

        local_files: list[str] = []
        for tar_bytes, stat in zip(files_content, files_stat):
            try:
                file_name, content = self._extract_from_tar(tar_bytes)
                local_path = os.path.join(local_output, file_name)
                #如果已存在则避免覆盖
                base, ext = os.path.splitext(local_path)
                counter = 1
                while os.path.exists(local_path):
                    local_path = f"{base}_{counter}{ext}"
                    counter += 1
                with open(local_path, "wb") as f:
                    f.write(content)
                logger.info(f"文件已保存: {local_path} (大小: {stat.get('size', '未知')} bytes)")
                local_files.append(local_path)

            except Exception as e:
                logger.error(f"保存文件失败: {e}")

        return local_files if local_files else None

    def _extract_from_tar(self, tar_bytes: bytes) -> tuple[str, bytes]:
        """解出tar流中的第一个文件，返回 (文件名, 内容)"""
        file_like = io.BytesIO(tar_bytes)
        with tarfile.open(fileobj=file_like, mode="r:") as tar:
            member = tar.getmembers()[0]
            f = tar.extractfile(member)
            if f is None:
                raise IOError("无法从tar中提取文件")
            return member.name, f.read()
