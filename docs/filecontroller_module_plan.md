# FileController Module

`FileController` provides advanced file and folder management, automation, and inspection. It is designed to handle file operations, batch processing, folder management, metadata inspection, and file system automation tasks.


## **1. File Operations**

| Function | Parameters | Description |
|----------|------------|-------------|
| `open_file(file_path, file_name=None)` | `file_path: str`, `file_name: str \| None` | Opens the specified file. Resolves name via registry if provided. |
| `copy_file(src_path, dest_path, overwrite=False)` | `src_path: str`, `dest_path: str`, `overwrite: bool` | Copies a file to a new location. Can overwrite existing files. |
| `move_file(src_path, dest_path, overwrite=False)` | `src_path: str`, `dest_path: str`, `overwrite: bool` | Moves a file to a new location. |
| `rename_file(file_path, new_name)` | `file_path: str`, `new_name: str` | Renames the file while keeping it in the same directory. |
| `delete_file(file_path, to_recycle_bin=True)` | `file_path: str`, `to_recycle_bin: bool` | Deletes the file. Can use recycle bin instead of permanent deletion. |
| `secure_delete(file_path, passes=3)` | `file_path: str`, `passes: int` | Overwrites file data before deletion for secure erasure. |


## **2. Folder Operations**

| Function | Parameters | Description |
|----------|------------|-------------|
| `open_folder(folder_path, folder_name=None, select_file=None)` | `folder_path: str`, `folder_name: str \| None`, `select_file: str \| None` | Opens a folder in Explorer, optionally selecting a file. |
| `create_folder(folder_path)` | `folder_path: str` | Creates a new folder at the specified path. |
| `delete_folder(folder_path, recursive=False, to_recycle_bin=True)` | `folder_path: str`, `recursive: bool`, `to_recycle_bin: bool` | Deletes a folder. Can delete recursively and send to recycle bin. |
| `list_folder_contents(folder_path, include_files=True, include_folders=True)` | `folder_path: str`, `include_files: bool`, `include_folders: bool` | Returns list of files/folders inside a folder. |
| `search_files(folder_path, pattern, recursive=True)` | `folder_path: str`, `pattern: str`, `recursive: bool` | Searches for files matching a pattern (supports regex/wildcards). |


## **3. File & Folder Validation / Inspection**

| Function | Parameters | Description |
|----------|------------|-------------|
| `validate_path(path)` | `path: str` | Checks if the path exists. |
| `get_metadata(file_path)` | `file_path: str` | Returns metadata: size, type, extension, created/modified/accessed times. |
| `calculate_hash(file_path, algorithm="md5")` | `file_path: str`, `algorithm: str` | Calculates hash (md5, sha1, sha256) for integrity checking. |
| `is_locked(file_path)` | `file_path: str` | Checks if the file is currently locked by another process. |
| `preview_file(file_path, lines=10)` | `file_path: str`, `lines: int` | Returns a text preview of first N lines for text files. |


## **4. Archive Operations**

| Function | Parameters | Description |
|----------|------------|-------------|
| `zip_files(file_paths, dest_zip)` | `file_paths: list[str]`, `dest_zip: str` | Compresses files/folders into a `.zip`. |
| `unzip_file(zip_path, extract_to)` | `zip_path: str`, `extract_to: str` | Extracts contents of a `.zip` archive. |


## **5. Advanced Automation / Watcher**

| Function | Parameters | Description |
|----------|------------|-------------|
| `watch_path(path, events, callback)` | `path: str`, `events: list[str]`, `callback: callable` | Watches for file system changes (`created`, `deleted`, `modified`, `renamed`) and triggers callback. |
| `batch_operation(paths, operation, **kwargs)` | `paths: list[str]`, `operation: str` | Performs an operation (copy, move, delete, etc.) on multiple files/folders in batch. |


## **Notes**

- All functions handle exceptions and return meaningful success/failure messages.
- Supports batch operations and multi-path handling.
- Intended for integration with automation engines or command listeners.
- Designed to extend registry-based path resolution and environment variable support.

