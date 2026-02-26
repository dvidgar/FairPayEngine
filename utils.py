import os
import warnings


def clear_dir(path: str) -> None:
    """check if upload path exists and empty it."""
    if os.path.exists(path):
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))

