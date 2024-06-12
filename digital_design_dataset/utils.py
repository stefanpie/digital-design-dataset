import os
import shutil
from pathlib import Path

from dotenv import load_dotenv


def auto_find_bin(bin_name: str) -> Path | None:
    # search in PATH
    bin_path = shutil.which(bin_name)
    if bin_path is not None:
        bin_path_obj = Path(bin_path)
        return bin_path_obj

    # search in local .env with key "<bin_name>_PATH"
    load_dotenv()
    bin_path_env = f"{bin_name}_PATH"
    bin_path_env_str = os.getenv(bin_path_env)
    if bin_path_env_str is not None:
        bin_path_obj = Path(bin_path_env_str)
        if bin_path_obj.exists():
            return bin_path_obj

    return None
