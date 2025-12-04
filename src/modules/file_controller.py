# file_handler.py
import os, subprocess, json
from pathlib import Path
from typing import Optional
from core.registry import action
from core.base_module import BaseModule
from core.registry import registry





class FileController(BaseModule):
    def __init__(self):
        self.registry = registry


    @action(name="open_file", params={"file_path", "file_name"})
    def open_file(self, file_path: str = None, file_name: str = None):
        if file_name:
            file_path = self.registry.get_path(file_name)

        if not file_path:
            return "File path not found."

        if not os.path.isfile(file_path):
            return "Path is not a file."
        try:
            os.startfile(file_path)  
            return self.success(f"File opened: {file_path}")
        except Exception as e:
            return self.failure(f"Error opening file {file_path}: {e}")


    @action(name="open_folder", params={"folder_path", "folder_name", "select_file"})
    def open_folder(self, folder_path: str = None, folder_name: str = None, select_file: Optional[str] = None):
        if folder_name:
            folder_path = self.registry.get_path(folder_name)

        if not folder_path:
            return "Folder path not found."

        if not os.path.isdir(folder_path):
            return "Path is not a directory."
        try:
            if select_file:
                file_to_select = Path(folder_path) / select_file
                if file_to_select.exists():
                    subprocess.run(["explorer", "/select,", str(file_to_select)])
                else:
                    return "File does not exists."
            else:
                os.startfile(folder_path)
            return self.success("Folder opened successfully.")
        except Exception as e:
            return (f"Error opening folder {folder_path}: {e}")


    @action(name="validate", params={"path"})
    def validate_path(self, path: str):
        exists = Path(path).exists()
        return self.success("Path validation successfull", data={"exists": exists})






