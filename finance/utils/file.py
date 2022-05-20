import errno
import os
import json
from typing import Union
from pathlib import Path


def make_dir(directory: Union[str, Path]) -> None:
    """Create a directory if it does not exist.

    Args:
        directory (str or Path): Path to the directory to create.
    """
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def read_json(path: Union[str, Path]) -> dict:
    """Read a json file and return a dictionary."""
    with open(path, "r") as file:
        config = json.load(file)
    return config


def save_json(obj: Union[dict, list], output_file: Union[str, Path], apply_json_formatting: bool = True) -> None:
    """Save a dictionary to disk in json format.

    Args:
        obj (dict or list): An json serialisable object.
        output_file (str or Path): A path to the json file that will be created.
        apply_json_formatting (bool): If True, the output json file will
           contain less white space. This is done using the format_json_string function.
           Defaults to True.
    """
    with open(output_file, "w") as file:
        json.dump(obj, file, indent=4)
