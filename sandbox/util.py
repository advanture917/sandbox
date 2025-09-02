import logging
import tempfile
from pathlib import Path

logger = logging.getLogger("llm_sandbox")
logging.basicConfig(level=logging.INFO)

def create_temp_dir(prefix="sandbox_") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))

