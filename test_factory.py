import unittest
from sandbox.backend.base import BackendFactory
from sandbox.backend.docker import DockerBackend
from sandbox.backend.k8s import K8sBackend
from sandbox.const import BackendType

class TestBackendFactory(unittest.TestCase):
    def test_register_backend(self):
        """测试注册后端"""
        # 注册后端
        BackendFactory.register_backend('docker', DockerBackend)
        BackendFactory.register_backend('kubernetes', K8sBackend)
        
        # 验证后端已注册
        backends = BackendFactory.get_available_backends()
        self.assertIn('docker', backends)
        self.assertIn('kubernetes', backends)
    
    def test_create_backend(self):
        """测试创建后端实例"""
        # 注册后端
        BackendFactory.register_backend('docker', DockerBackend)
        
        # 创建后端实例
        backend = BackendFactory.create_backend('docker')
        self.assertIsInstance(backend, DockerBackend)
    
    def test_create_unsupported_backend(self):
        """测试创建不支持的后端"""
        with self.assertRaises(ValueError):
            BackendFactory.create_backend('unsupported')

if __name__ == '__main__':
    unittest.main()