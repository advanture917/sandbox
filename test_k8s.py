from sandbox.session import SandboxSession
from sandbox.const import BackendType
with SandboxSession(backend_type = BackendType.KUBERNETES) as ss:
    command = "pwdsss"
    result = ss.exe_command(command)
    print("stdout:", result)