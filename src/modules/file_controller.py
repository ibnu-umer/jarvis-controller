import os, zipfile
import shutil
import subprocess, fnmatch
from pathlib import Path
from typing import Optional, List
import hashlib
import send2trash  # for safe deletion
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import List

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


    @action(name="create_folder", params={"folder_path"})
    def create_folder(self, folder_path: str):
        try:
            if not folder_path:
                return self.failure("Folder path is required.")

            if os.path.exists(folder_path):
                return self.failure("Folder already exists.")

            os.makedirs(folder_path, exist_ok=True)
            return self.success(f"Folder created: {folder_path}")
        except Exception as e:
            return self.failure(f"Error creating folder: {e}")
        

    @action(name="delete_folder", params={"folder_path", "recursive", "to_recycle_bin"})
    def delete_folder(self, folder_path: str, recursive: bool = False, to_recycle_bin: bool = True):
        try:
            if not os.path.isdir(folder_path):
                return self.failure("Folder does not exist.")

            if to_recycle_bin:
                send2trash.send2trash(folder_path)
            else:
                if recursive:
                    shutil.rmtree(folder_path)
                else:
                    os.rmdir(folder_path)

            return self.success(f"Folder deleted: {folder_path}")
        except Exception as e:
            return self.failure(f"Error deleting folder: {e}")
        

    @action(name="list_folder_contents", params={"folder_path", "include_files", "include_folders"})
    def list_folder_contents(self, folder_path: str, include_files: bool = True, include_folders: bool = True):
        try:
            if not os.path.isdir(folder_path):
                return self.failure("Folder path is invalid.")

            files = []
            folders = []

            for entry in os.scandir(folder_path):
                if entry.is_file() and include_files:
                    files.append(entry.name)
                if entry.is_dir() and include_folders:
                    folders.append(entry.name)

            return self.success("Folder contents retrieved.", {"files": files, "folders": folders})

        except Exception as e:
            return self.failure(f"Error reading folder contents: {e}")
        

    @action(name="search_files", params={"folder_path", "pattern", "recursive"})
    def search_files(self, folder_path: str, pattern: str, recursive: bool = True):
        try:
            if not os.path.isdir(folder_path):
                return self.failure("Folder path is invalid.")

            matches = []

            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # check files
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            matches.append(os.path.join(root, file))

                    # check folders
                    for d in dirs:
                        if fnmatch.fnmatch(d, pattern):
                            matches.append(os.path.join(root, d))
            else:
                for entry in os.scandir(folder_path):
                    if fnmatch.fnmatch(entry.name, pattern):
                        matches.append(entry.path)

            return self.success("Search completed.", {"results": matches})

        except Exception as e:
            return self.failure(f"Error searching files: {e}")
            

    # ------------------------- VALIDATION ------------------------- #

    @action(name="validate_path", params={"path"})
    def validate_path(self, path: str):
        try:
            p = Path(path).expanduser()
            return self.success("Path validated.", data={"exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir()})
        except Exception as e:
            return self.failure("Path validation failed.", data={"error": str(e)})


    @action(name="get_metadata", params={"file_path"})
    def get_metadata(self, file_path: str):
        try:
            if not Path(file_path).exists():
                return self.failure("File does not exist.")

            stat = Path(file_path).stat()
            metadata = {
                "name": Path(file_path).name,
                "type": "directory" if Path(file_path).is_dir() else "file",
                "extension": Path(file_path).suffix if Path(file_path).is_file() else None,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_birthtime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            }

            return self.success("Metadata retrieved.", {"metadata": metadata})
        except Exception as e:
            return self.failure(f"Error fetching metadata: {e}")


    @action(name="calculate_hash", params={"file_path", "algorithm"})
    def calculate_hash(self, file_path: str, algorithm: str = "md5"):
        try:
            if not os.path.isfile(file_path):
                return self.failure("File not found or not a file.")

            if algorithm.lower() not in ["md5", "sha1", "sha256"]:
                return self.failure("Unsupported hash algorithm.")

            hash_func = getattr(hashlib, algorithm.lower())()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)

            return self.success("Hash calculated.", {"hash": hash_func.hexdigest()})
        except Exception as e:
            return self.failure(f"Error calculating hash: {e}")


    @action(name="is_locked", params={"file_path"})
    def is_locked(self, file_path: str):
        try:
            if not os.path.isfile(file_path):
                return self.failure("File does not exist.")

            locked = False
            try:
                with open(file_path, "a"):
                    pass
            except PermissionError:
                locked = True

            return self.success("Lock status read.", {"locked": locked})
        except Exception as e:
            return self.failure(f"Error checking lock status: {e}")


    @action(name="preview_file", params={"file_path", "lines"})
    def preview_file(self, file_path: str, lines: int = 10):
        try:
            if not os.path.isfile(file_path):
                return self.failure("File does not exist.")

            # reject binary files automatically
            with open(file_path, "rb") as f:
                if b"\0" in f.read(2048):  # crude binary detection
                    return self.failure("Cannot preview binary file.")

            content = []
            with open(file_path, "r", errors="ignore") as f:
                for _ in range(lines):
                    line = f.readline()
                    if not line:
                        break
                    content.append(line.rstrip("\n"))

            return self.success("Preview loaded.", {"preview": content})
        except Exception as e:
            return self.failure(f"Error previewing file: {e}")


    # ------------------------- ARCHIVE ------------------------- #

    @action(name="zip_files", params={"file_paths", "dest_zip"})
    def zip_files(self, file_paths: list[str], dest_zip: str):
        try:
            if not file_paths or not isinstance(file_paths, list):
                return self.failure("file_paths must be a non-empty list.")

            dest_zip = str(dest_zip)

            # ensure directory exists
            dest_dir = os.path.dirname(dest_zip)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for path in file_paths:
                    if not Path(path).exists():
                        continue

                    if Path(path).is_dir():
                        for root, _, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, Path(path).parent)
                                zipf.write(full_path, arcname)
                    else:
                        arcname = os.path.basename(path)
                        zipf.write(path, arcname)

            return self.success("Files zipped successfully.", {"zip_path": dest_zip})
        except Exception as e:
            return self.failure(f"Error creating zip: {e}")
        

    @action(name="unzip_file", params={"zip_path", "extract_to"})
    def unzip_file(self, zip_path: str, extract_to: str):
        try:
            if not os.path.isfile(zip_path):
                return self.failure("Zip file not found.")

            if not os.path.exists(extract_to):
                os.makedirs(extract_to, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(extract_to)

            return self.success("Zip extracted successfully.", {"extracted_to": extract_to})
        except Exception as e:
            return self.failure(f"Error extracting zip: {e}")
        

    # ------------------------- ADVANCED ------------------------- #

    @action(name="watch_path", params={"path", "events"})
    def watch_path(self, path: str, events: list[str]):
        if not os.path.exists(path):
            return self.failure("Path does not exist.")
        
        def callback(changed_path, event_type):
            print(f"Event: {event_type}, Path: {changed_path}")

        class WatchHandler(FileSystemEventHandler):
            def dispatch(self, event):
                event_type = None

                if event.event_type == "created" and "created" in events:
                    event_type = "created"
                elif event.event_type == "deleted" and "deleted" in events:
                    event_type = "deleted"
                elif event.event_type == "modified" and "modified" in events:
                    event_type = "modified"
                elif event.event_type == "moved" and "renamed" in events:
                    event_type = "renamed"

                if event_type:
                    callback(event.src_path, event_type)

        try:
            observer = Observer()
            observer.schedule(WatchHandler(), path, recursive=True)
            observer.start()
            return self.success("Watcher started.")
        except Exception as e:
            return self.failure(f"Failed to watch path: {e}")
        

    @action(name="batch_operation", params={"paths", "operation"})
    def batch_operation(self, paths: List[str], operation: str, **kwargs):
        valid_ops = ["copy", "move", "delete"]

        if operation not in valid_ops:
            return self.failure(f"Invalid operation. Allowed: {valid_ops}")

        results = {"success": [], "failed": []}

        for p in paths:
            try:
                if not os.path.exists(p):
                    results["failed"].append((p, "Not found"))
                    continue

                if operation == "delete":
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)

                elif operation == "copy":
                    dest = kwargs.get("dest")
                    if not dest:
                        results["failed"].append((p, "Missing dest"))
                        continue
                    if os.path.isdir(p):
                        shutil.copytree(p, os.path.join(dest, os.path.basename(p)))
                    else:
                        shutil.copy2(p, dest)

                elif operation == "move":
                    dest = kwargs.get("dest")
                    if not dest:
                        results["failed"].append((p, "Missing dest"))
                        continue
                    shutil.move(p, dest)

                results["success"].append(p)

            except Exception as e:
                results["failed"].append((p, str(e)))

        return self.success("Batch operation completed.", results)

