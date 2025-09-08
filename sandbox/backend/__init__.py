from .base import Backend, BackendFactory
from .docker import DockerBackend
from .k8s import K8sBackend

# 注册后端实现
BackendFactory.register_backend('docker', DockerBackend)
BackendFactory.register_backend('kubernetes', K8sBackend)