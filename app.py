import gradio as gr
from sandbox.session import SandboxSession
from sandbox.const import SupportedLanguage
from sandbox.util import logger
from sandbox.backend.base import BackendFactory
from sandbox.backend.docker import DockerBackend
from sandbox.backend.k8s import K8sBackend
from sandbox.const import BackendType
def run_code_ui(code: str, language: str, libraries: str,file_path : list[str]|str =None) -> str:
    """
    用于Gradio界面的代码执行函数
    将用户输入转换为合适的格式并调用沙箱执行
    """
    try:
        # 处理依赖库列表
        libs = None
        if libraries.strip():
            # 分割逗号并去除空格和空字符串
            libs = [lib.strip() for lib in libraries.split(',') if lib.strip()]
        fps = None

        if file_path.strip():
            # 分割逗号并去除空格和空字符串
            fps = [fps.strip() for fps in file_path.split(',') if fps.strip()]
        logger.info(f"🔥{fps}")
        # 验证语言类型
        if language not in SupportedLanguage.__members__:
            return f"错误: 不支持的语言 {language}\n支持的语言: {list(SupportedLanguage.__members__.keys())}"
        import time
        # 执行代码
        with SandboxSession(language=SupportedLanguage[language]) as session:
            result = session.run_code(code=code, dependencies=libs,file_path=fps)
            if file_path is not  None:
                logger.info(f"🤩{file_path}")
                time.sleep(30)
            return f"执行结果:\n{result}" if file_path == ""  else f"已生成{result}"

    except Exception as e:
        return f"执行出错: {str(e)}"


# 创建Gradio界面
with gr.Blocks(title="代码沙箱执行环境") as demo:
    gr.Markdown("# 代码沙箱执行环境")
    gr.Markdown("> 在此处输入代码并执行，支持多种编程语言（当前主要支持Python）")

    with gr.Row():
        with gr.Column(scale=4):
            code_input = gr.Code(
                label="代码输入",
                value="print('Hello, World!')\nprint('1+1 =', 1+1)",
                language="python"
            )

            language_select = gr.Dropdown(
                label="编程语言",
                choices=list(SupportedLanguage.__members__.keys()),  # ['PYTHON', 'JAVA', ...]
                value="PYTHON"
            )

            libraries_input = gr.Textbox(
                label="依赖库（逗号分隔）",
                placeholder="例如: numpy, pandas, matplotlib",
                value=""
            )
            file_path_input = gr.Textbox(
                label="生成文件名",
                placeholder="例如: test.txt,xxx.png",
                value=""
            )
        with gr.Column(scale=2):
            output = gr.Textbox(
                label="执行结果",
                lines=15,
                interactive=False
            )

    run_btn = gr.Button("执行代码", variant="primary")
    clear_btn = gr.Button("清空")

    # 设置事件
    run_btn.click(
        fn=run_code_ui,
        inputs=[code_input, language_select, libraries_input,file_path_input],
        outputs=output
    )

    clear_btn.click(
        fn=lambda: ("", "", ""),
        inputs=[],
        outputs=[code_input, libraries_input, output]
    )

if __name__ == "__main__":
    # BackendFactory.register_backend('docker', DockerBackend)
    BackendFactory.register_backend('kubernetes', K8sBackend)
    demo.launch(debug=True)

