import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from sandbox.session import SandboxSession
from sandbox.const import BackendType, SupportedLanguage
from sandbox.data import CommandResult
from sandbox.util import logger


class SandboxLLM:
    def __init__(
        self,
        backend_type: BackendType = BackendType.DOCKER,
        model_name: str = "Qwen/Qwen3-30B-A3B-Thinking-2507",
        base_url: str = "",
        api_key: str = "",
        language: SupportedLanguage = SupportedLanguage.PYTHON,
    ):
        self.backend_type = backend_type
        self.language = language
        self.llm = ChatOpenAI(
            model_name=model_name, base_url=base_url, api_key=api_key, temperature=0
        )

        # --- Prompt 模板 ---
        self.prompt_initial = PromptTemplate.from_template(
            "You are a {language} code generator. Generate complete {language} code "
            "to accomplish the following task:\n\n"
            "{task}\n\n"
            "Additionally, list any required dependencies (libraries/modules).\n\n"
            "Return the result strictly in JSON with the following structure:\n"
            "{{\"code\": \"<code string>\", \"dependencies\": [\"lib1\", \"lib2\"]}}"
        )

        self.prompt_fix_error = PromptTemplate.from_template(
            "The following {language} code failed for the task:\n\n{task}\n\n"
            "Error details:\n{stderr}\n\n"
            "Please fix the code and update the dependencies if needed.\n\n"
            "Return strictly in JSON format:\n"
            "{{\"code\": \"<corrected code>\", \"dependencies\": [\"lib1\", \"lib2\"]}}"
        )

        self.prompt_fix_result = PromptTemplate.from_template(
            "The following {language} code ran for the task:\n\n{task}\n\n"
            "But the output did not match the expected result.\n"
            "Expected output should contain: {expected_output}\n\n"
            "Actual stdout:\n{stdout}\n\n"
            "Please modify the code (and dependencies if needed) to produce the correct output.\n\n"
            "Return strictly in JSON format:\n"
            "{{\"code\": \"<corrected code>\", \"dependencies\": [\"lib1\", \"lib2\"]}}"
        )

    def _generate_code(self, task: str, result: CommandResult | None, expected_output: str | None):
        if result is None:
            prompt = self.prompt_initial
            variables = {
                "task": task,
                "language": self.language.value,
            }
        elif result.exit_code != 0:
            prompt = self.prompt_fix_error
            variables = {
                "task": task,
                "language": self.language.value,
                "stderr": result.stderr,
            }
        else:
            prompt = self.prompt_fix_result
            variables = {
                "task": task,
                "language": self.language.value,
                "stdout": result.stdout,
                "expected_output": expected_output or "",
            }

        return (prompt | self.llm).invoke(variables)

    def _parse_llm_output(self, raw_output) -> dict:
        """
        确保 LLM 输出能被解析为 {"code": str, "dependencies": list[str]}。
        """
        if hasattr(raw_output, "content"):
            text = raw_output.content
        else:
            text = str(raw_output)

        try:
            parsed = json.loads(text)
            code = parsed.get("code", "")
            dependencies = parsed.get("dependencies", [])
            if not isinstance(dependencies, list):
                dependencies = []
            return {"code": code, "dependencies": dependencies}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM output as JSON: {text}")
            return {"code": text, "dependencies": []}

    def run_code(
        self, task: str, expected_output: str | None = None, max_retries: int = 3
    ) -> CommandResult:
        result = None
        with SandboxSession(
            backend_type=self.backend_type, language=self.language
        ) as sb:
            for attempt in range(max_retries + 1):
                raw_output = self._generate_code(task, result, expected_output)
                parsed = self._parse_llm_output(raw_output)

                code = parsed["code"]
                dependencies = parsed["dependencies"]
                logger.info(f"⬆️{code}")
                logger.info(f"⬆️{dependencies}")
                logger.info(f"🤡 Attempt {attempt + 1}, deps={dependencies}")
                result = sb.run_code(code=code, dependencies=dependencies)

                if result.exit_code == 0 and (
                    expected_output is None or expected_output in result.stdout
                ):
                    return result

                print(
                    f"Attempt {attempt + 1} failed. Exit: {result.exit_code}, stderr: {result.stderr}"
                )

        return result
