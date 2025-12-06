import os
import shutil
import subprocess, win32com, pythoncom
from pathlib import Path
from typing import Optional, List
import hashlib
import send2trash  # for safe deletion

from core.base_module import BaseModule
from core.registry import registry, action


class FileController(BaseModule):
    def __init__(self):
        self.registry = registry

    # ------------------------- FILE OPERATIONS ------------------------- #

    @action(name="open_file", params={"file_path", "file_name", "with_app"})
    def open_file(self, file_path: str = None, file_name: str = None, with_app: str = None):
        try:
            if file_name:
                file_path = self.registry.get_path(file_name)

            if not file_path:
                return self.failure("File path not provided.")

            file_path = Path(os.path.expandvars(file_path)).expanduser().resolve()

            if not file_path.exists() or not file_path.is_file():
                return self.failure(f"File does not exist or is not a file: {file_path}")

            if with_app:
                app_path = self.registry.get_path(with_app)
                if not app_path:
                    return self.failure(f"App not registered: {with_app}")
                subprocess.Popen([app_path, str(file_path)])
            else:
                os.startfile(str(file_path))

            return self.success(f"Opened file successfully.", data={"path": str(file_path)})

        except Exception as e:
            return self.failure("Failed to open file.", data={"error": str(e)})


    @action(name="copy_file", params={"src_path", "dest_path", "overwrite"})
    def copy_file(self, src_path: str, dest_path: str, overwrite: bool = False):
        try:
            src = Path(src_path).expanduser().resolve()
            dest = Path(dest_path).expanduser().resolve()

            if not src.exists() or not src.is_file():
                return self.failure("Source file does not exist.")

            if dest.exists() and not overwrite:
                return self.failure("Destination file already exists and overwrite is disabled.")

            shutil.copy2(src, dest)
            return self.success("File copied successfully.", data={"destination": str(dest)})
        except Exception as e:
            return self.failure("Copy operation failed.", data={"error": str(e)})


    @action(name="move_file", params={"src_path", "dest_path", "overwrite"})
    def move_file(self, src_path: str, dest_path: str, overwrite: bool = False):
        try:
            src = Path(src_path).expanduser().resolve()
            dest = Path(dest_path).expanduser().resolve()

            if not src.exists() or not src.is_file():
                return self.failure("Source file does not exist.")

            if dest.exists() and not overwrite:
                return self.failure("Destination already exists and overwrite disabled.")

            shutil.move(str(src), str(dest))
            return self.success("File moved successfully.", data={"destination": str(dest)})
        except Exception as e:
            return self.failure("Move operation failed.", data={"error": str(e)})


    @action(name="rename_file", params={"file_path", "new_name"})
    def rename_file(self, file_path: str, new_name: str):
        try:
            file = Path(file_path).expanduser().resolve()
            if not file.exists() or not file.is_file():
                return self.failure("File does not exist.")

            new_path = file.with_name(new_name)
            file.rename(new_path)

            return self.success("File renamed successfully.", data={"new_path": str(new_path)})
        except Exception as e:
            return self.failure("Rename failed.", data={"error": str(e)})


    @action(name="delete_file", params={"file_path", "to_recycle_bin"})
    def delete_file(self, file_path: str, to_recycle_bin: bool = True):
        try:
            file = Path(file_path).expanduser().resolve()

            if not file.exists() or not file.is_file():
                return self.failure("File does not exist.")

            if to_recycle_bin:
                send2trash.send2trash(str(file))
            else:
                file.unlink()

            return self.success("File deleted successfully.", data={"path": str(file)})
        except Exception as e:
            return self.failure("File deletion failed.", data={"error": str(e)})


    # ------------------------- FOLDER OPERATIONS ------------------------- #

    @action(name="open_folder", params={"folder_path", "folder_name", "select_file", "focus"})
    def open_folder(self, folder_path: str = None, folder_name: str = None, select_file: Optional[str] = None, focus: bool = True):
        try:
            if folder_name:
                folder_path = self.registry.get_path(folder_name)

            if not folder_path:
                return self.failure("Folder path not provided.")

            folder = Path(folder_path).expanduser().resolve()

            if not folder.exists() or not folder.is_dir():
                return self.failure("Folder does not exist.")

            if select_file:  # always focused
                target = folder / select_file
                if not target.exists():
                    return self.failure("File to select does not exist.")
                subprocess.run(["explorer", "/select,", str(target)])
            elif focus:
                subprocess.Popen(['explorer', str(folder)])
            else:
                os.startfile(str(folder))  # probably in the background

            return self.success("Folder opened.", data={"path": str(folder)})

        except Exception as e:
            return self.failure("Failed to open folder.", data={"error": str(e)})


    # ------------------------- VALIDATION ------------------------- #

    @action(name="validate_path", params={"path"})
    def validate_path(self, path: str):
        try:
            p = Path(path).expanduser()
            return self.success("Path validated.", data={"exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir()})
        except Exception as e:
            return self.failure("Path validation failed.", data={"error": str(e)})







