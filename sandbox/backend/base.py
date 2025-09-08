from typing import Any
from sandbox.data import ExecutionRequest

class Backend:
    def create_container(self, lang: str,  **kwargs):
       ...
    def start_container(self, container: Any) -> None:
        """Start  container."""
        ...
    def stop_container(self, container: Any) -> None:
        """Stop  container."""
        ...
    def execute_command(self, container: Any, command: str, **kwargs: Any) -> 'CommandResult':
        ...

    def run_code(self,container:Any , req:ExecutionRequest):
        ...

    def remove_container (self,container :Any):
        pass

class BackendFactory:
    _backends = {}
    
    @classmethod
    def register_backend(cls, name: str, backend_class: type[Backend]):
        """注册一个新的后端实现"""
        cls._backends[name] = backend_class
    
    @classmethod
    def create_backend(cls, name: str, *args, **kwargs) -> Backend:
        """创建一个后端实例"""
        backend_class = cls._backends.get(name)
        if not backend_class:
            raise ValueError(f"Unsupported backend: {name}")
        return backend_class(*args, **kwargs)
    
    @classmethod
    def get_available_backends(cls):
        """获取所有可用的后端"""
        return list(cls._backends.keys())

