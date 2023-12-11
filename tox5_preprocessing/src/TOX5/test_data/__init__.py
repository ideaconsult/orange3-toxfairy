import importlib.resources
import os
from typing import List

loc = importlib.resources.files(__package__)


def get_dirs() -> List[str]:
    """
        Get a list of subdirectories in the specified location.

        Returns:
            List[str]: A list of subdirectory names, excluding special directories like '__pycache__'.
        """
    return [f for f in os.listdir(loc) if
            os.path.isdir(os.path.join(loc, f)) and not f.startswith(
                '__') and f != '__pycache__']


def get_files_from_dir(directory: str) -> List[str]:
    """
        Get a list of file names in the specified directory.

        Args:
            directory (str): The name of the directory.

        Returns:
            List[str]: A list of file names in the specified directory.
        """
    return [f for f in os.listdir(os.path.join(loc, directory)) if
            os.path.isfile(os.path.join(loc, directory, f))]
