from kubernetes import client, config


def deploy_docker_image(image_path, deployment_name, app_label, replicas=1, container_port=80, node_name=None):
    # 加载kubeconfig配置
    config.load_kube_config()

    # 创建API客户端
    apps_v1 = client.AppsV1Api()

    # 定义容器
    container = client.V1Container(
        name="app-container",
        image=image_path,
        ports=[client.V1ContainerPort(container_port=container_port)],
        command=["tail" ,"-f" ,"/dev/null"]
    )

    # 定义Pod模板
    pod_spec = client.V1PodSpec(
        containers=[container]
    )

    # 如果指定节点，则加上 nodeName
    if node_name:
        pod_spec.node_name = node_name

    # 定义Deployment
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
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
        apps_v1.delete_namespaced_deployment(
            name=deployment_name, namespace="default"
        )
        print(f"旧的 Deployment {deployment_name} 已删除，准备创建新的...")
    except client.exceptions.ApiException as e:
        if e.status != 404:
            print(f"删除旧 Deployment 失败: {e}")

    # 创建新的 Deployment
    response = apps_v1.create_namespaced_deployment(
        namespace="default",
        body=deployment
    )
    print(f"Deployment 创建成功: {response.metadata.name}")
    return response


if __name__ == "__main__":
    IMAGE_PATH = "ghcr.io/advanture917/sandbox/python:latest"
    DEPLOYMENT_NAME = "my-python-deploy"
    APP_LABEL = "my-app"
    REPLICAS = 2
    CONTAINER_PORT = 80

    # 指定运行的节点名（kubectl get nodes 查看）
    NODE_NAME = None
    #v1 = client.AppsV1Api()
    #deploy_docker_image(IMAGE_PATH, DEPLOYMENT_NAME, APP_LABEL, REPLICAS, CONTAINER_PORT, NODE_NAME)
    from kubernetes import client, config
    from kubernetes.stream import stream

    config.load_kube_config()  # 集群内
    v1 = client.CoreV1Api()
    namespace = "default"
    pods = v1.list_namespaced_pod(namespace, label_selector="app=my-app")
    running_pods = [p for p in pods.items if p.status.phase == "Running"]
    pod_name = running_pods[0].metadata.name

    resp = stream(v1.connect_get_namespaced_pod_exec,
                  pod_name,
                  namespace,
                  command=["pwd"],
                  stderr=True, stdin=False,
                  stdout=True, tty=False)
    print(resp)
