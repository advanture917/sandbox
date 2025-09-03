import logging
import tempfile
from pathlib import Path

logger = logging.getLogger("llm_sandbox")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# def create_temp_dir(prefix="sandbox_") -> Path:
#     return Path(tempfile.mkdtemp(prefix=prefix))

