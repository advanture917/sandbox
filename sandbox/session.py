import docker
from sandbox.const import BackendType,SupportedLanguage
from sandbox.backend.base import Backend
from sandbox.backend.docker import DockerBackend
from sandbox.errors import  BackendError,BackendNotAvailable
from sandbox.util import logger
from sandbox.data import ExecutionRequest
from typing import Any
class SandboxSession:
    def __init__(
            self,
            backend:BackendType = BackendType.DOCKER,
            language:SupportedLanguage = SupportedLanguage.PYTHON):
        self.backend_type = backend
        self.language = language
        self.backend = None
        self.container = None

    def __enter__(self):
        """进入上下文时启动 backend"""
        if self.backend_type == BackendType.DOCKER:
            client = docker.from_env()
            self.backend = DockerBackend(client=client)
        else:
            raise BackendNotAvailable(f"Backend {self.backend_type} not implemented")

        logger.info(f"Creating container for language={self.language}")
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

    def exe_command(self,command:str,**kwargs:Any):
        return self.backend.execute_command(self.container,command,**kwargs)
    def run_code(self,code:str, dependencies: list[str] | None = None):
        request = ExecutionRequest(
            code=code,
            language=self.language,
            dependencies=dependencies,
        )
        return self.backend.run_code(self.container, request)

