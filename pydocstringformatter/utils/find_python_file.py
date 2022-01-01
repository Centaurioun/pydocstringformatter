import os
from pathlib import Path


def _is_python_file(filename: str) -> bool:
    return filename.endswith(".py")


def _find_python_files(filenames: list[str], recursive: bool = True) -> list[Path]:
    """Find all python files for a list of potential file and directory names"""
    pathnames: list[Path] = []

    for name in filenames:
        if os.path.isdir(name):
            if recursive:
                for root, _, children in os.walk(name):
                    pathnames += [
                        Path(os.path.abspath(root)) / child
                        for child in children
                        if _is_python_file(child)
                    ]
            else:
                pathnames += [
                    file for file in Path(name).iterdir() if _is_python_file(str(file))
                ]
        else:
            pathnames.append(Path(name))

    return sorted(pathnames)