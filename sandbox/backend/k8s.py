from typing import Any
from sandbox.backend.base import Backend
from sandbox.data import ExecutionRequest
from sandbox.const import DefaultImage, SupportedLanguage
import kubernetes
from kubernetes import client, config
import uuid
import base64
from sandbox.util import logger

class K8sBackend(Backend):
    def __init__(self, namespace: str = "default"):
        # 加载kubeconfig
        try:
            config.load_kube_config()
        except:
            # 如果在集群内部运行，使用集群配置
            config.load_incluster_config()
        
        self.namespace = namespace
        self.apps_v1_api = client.AppsV1Api()
        self.core_v1_api = client.CoreV1Api()
        # 语言到镜像的映射关系
        self.lang_to_image = {
            SupportedLanguage.PYTHON: DefaultImage.PYTHON,
            SupportedLanguage.GO: DefaultImage.GO,
            SupportedLanguage.JAVA: DefaultImage.JAVA,
            SupportedLanguage.JAVASCRIPT: DefaultImage.JAVASCRIPT,
            SupportedLanguage.CPP: DefaultImage.CPP,
            SupportedLanguage.RUBY: DefaultImage.RUBY,
            SupportedLanguage.R: DefaultImage.R
        }
    
    def create_container(self, lang: str, **kwargs):
        """根据语言创建对应的Deployment"""
        # 这里需要根据语言选择合适的镜像
        image = self._get_image_for_language(lang)
        
        # 生成唯一的Deployment名称
        deployment_name = f'sandbox-{lang.lower()}-{uuid.uuid4().hex[:8]}'
        app_label = f'sandbox-{lang.lower()}'
        
        # 定义容器
        container = client.V1Container(
            name="sandbox-container",
            image=image,
            command=["tail", "-f", "/dev/null"]
        )

        # 定义Pod模板
        pod_spec = client.V1PodSpec(
            containers=[container]
        )

        # 定义Deployment
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_label}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app_label}),
                    spec=pod_spec
                )
            )
        )

        try:
            # 先尝试删除旧的 Deployment
            self.apps_v1_api.delete_namespaced_deployment(
                name=deployment_name, namespace=self.namespace
            )
        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise e

        # 创建新的 Deployment
        resp = self.apps_v1_api.create_namespaced_deployment(
            namespace=self.namespace,
            body=deployment
        )
        
        # 等待Deployment创建完成并获取Pod
        pod = self._wait_for_pod_running(app_label)
        return pod
    
    def start_container(self, container: Any) -> None:
        """启动容器（Deployment已经在运行）"""
        # Deployment在创建时就已经启动，这里可以添加等待Pod就绪的逻辑
        pass
    
    def stop_container(self, container: Any) -> None:
        """停止容器（删除Deployment）"""
        # 从Pod信息中获取Deployment名称
        deployment_name = container.metadata.labels.get('app', '').replace('sandbox-', 'sandbox-')
        if deployment_name:
            try:
                self.apps_v1_api.delete_namespaced_deployment(name=deployment_name, namespace=self.namespace)
            except client.exceptions.ApiException as e:
                if e.status != 404:
                    raise e
    
    def execute_command(self, container: Any, command: str, **kwargs: Any) -> 'CommandResult':
        """在Pod中执行命令"""
        from sandbox.data import CommandResult
        
        name = container.metadata.name
        
        # 执行命令
        exec_command = [
            '/bin/sh',
            '-c',
            command
        ]
        
        resp = kubernetes.stream.stream(
            self.core_v1_api.connect_get_namespaced_pod_exec,
            name,
            self.namespace,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _preload_content=False
        )
        
        # 等待命令执行完成
        resp.run_forever()
        # 获取执行结果
        exit_code = resp.returncode or 0
        logger.info(f'{exit_code}')
        stdout = resp.read_stdout()
        stderr = resp.read_stderr()
        logger.info(f'stderr {stderr}')
        return CommandResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
    
    def run_code(self, container: Any, req: ExecutionRequest) -> 'CommandResult':
        """在Kubernetes容器中运行代码"""
        code = req.code
        language = req.language
        libraries = req.dependencies
        
        # 处理包依赖
        if libraries is not None:
            install_command = self._get_install_command(language=language, libraries=libraries)
            self.execute_command(container, " ".join(install_command))
        
        # 创建代码文件
        file_path = self._create_file(container, code, language)
        
        # 执行代码
        command = self._get_run_command(file_path=file_path, language=language)
        result = self.execute_command(container, " ".join(command))
        
        return result
    
    def remove_container(self, container: Any):
        """删除容器（删除Deployment）"""
        # 从Pod信息中获取Deployment名称
        app_label = container.metadata.labels.get('app', '')
        deployment_name = app_label
        if deployment_name:
            try:
                self.apps_v1_api.delete_namespaced_deployment(name=deployment_name, namespace=self.namespace)
            except client.exceptions.ApiException as e:
                if e.status != 404:
                    raise e
    
    def _get_image_for_language(self, lang: str) -> str:
        """根据语言获取对应的镜像"""
        # 使用const.py中定义的镜像配置
        return self.lang_to_image.get(lang.lower(), "ubuntu:latest")
    
    def _wait_for_pod_running(self, app_label: str):
        """等待Pod运行"""
        import time
        for _ in range(100):  # 最多等待30秒
            pods = self.core_v1_api.list_namespaced_pod(namespace=self.namespace, label_selector=f"app={app_label}")
            running_pods = [p for p in pods.items if p.status.phase == "Running"]
            if running_pods:
                return running_pods[0]
            time.sleep(1)
        raise Exception(f"Pod with label {app_label} did not start in time")
    
    def _get_install_command(self, language: SupportedLanguage = SupportedLanguage.PYTHON, libraries: list[str] = None) -> list[str]:
        match language:
            case SupportedLanguage.PYTHON:
                # pip install 直接接收列表元素作为参数
                return ["pip", "install", "--quiet"] + libraries

            case SupportedLanguage.GO:
                # go get 接收包名列表
                return ["go", "get"] + libraries
            case SupportedLanguage.JAVA:
                # Java的依赖处理可能需要Maven或Gradle，这里简化处理
                return ["echo", "Java dependencies not implemented"]
            case SupportedLanguage.JAVASCRIPT:
                # npm install
                return ["npm", "install"] + libraries
            case SupportedLanguage.CPP:
                # C++的依赖处理可能需要apt-get或其他包管理器，这里简化处理
                return ["echo", "C++ dependencies not implemented"]
            case SupportedLanguage.RUBY:
                # gem install
                return ["gem", "install"] + libraries
            case SupportedLanguage.R:
                # R的依赖处理可能需要install.packages，这里简化处理
                return ["echo", "R dependencies not implemented"]
            case _:
                raise ValueError(f"不支持的语言: {language}")

    def _create_file(self, container: Any, code: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> str:
        file_ext = {
            SupportedLanguage.PYTHON: ".py",
            SupportedLanguage.GO: ".go",
            SupportedLanguage.JAVA: ".java",
            SupportedLanguage.JAVASCRIPT: ".js",
            SupportedLanguage.CPP: ".cpp",
            SupportedLanguage.RUBY: ".rb",
            SupportedLanguage.R: ".R",
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
        self.execute_command(container, " ".join(command))
        return file_path
    
    def _get_run_command(self, file_path: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> list[str]:
        """生成代码执行命令"""
        match language:
            case SupportedLanguage.PYTHON:
                return ["python", file_path]
            case SupportedLanguage.GO:
                return ["go", "run", file_path]
            case SupportedLanguage.JAVA:
                # Java需要先编译再运行，这里简化处理
                return ["java", file_path]
            case SupportedLanguage.JAVASCRIPT:
                return ["node", file_path]
            case SupportedLanguage.CPP:
                # C++需要先编译再运行，这里简化处理
                return ["./a.out"]
            case SupportedLanguage.RUBY:
                return ["ruby", file_path]
            case SupportedLanguage.R:
                return ["Rscript", file_path]