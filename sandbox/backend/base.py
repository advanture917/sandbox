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
    def execute_command(self, container: Any, command: str, **kwargs: Any) -> tuple[int, Any]:
        ...

    def run_code(self,container:Any , req:ExecutionRequest):
        ...

    def remove_container (self,container :Any):
        pass

