
TEMPLATE_REGISTRY = {}

def template(name=None, params=None):
    def wrapper(func):
        TEMPLATE_REGISTRY[name or func.__name__] = {
            "module": func.__module__,
            "function": func.__name__,
            "params": params or {}
        }
        return func
    return wrapper



@template(name="prepare_work_environment")
def prepare_work_environment() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "prepare_work_environment",
            "goal": "Prepare my work environment",
            "description": "Open project folder and launch editor",
            "entry": "check_workspace",
            "nodes": {
                "check_workspace": {
                    "type": "decision",
                    "condition": "workspace_ready",
                    "on_true": "done",
                    "on_false": "open_folder"
                },
                "open_folder": {
                    "type": "action",
                    "controller": "open_folder",
                    "args": {"path": "~/projects/jarvis"},
                    "retries": 1,
                    "on_success": "launch_vscode",
                    "on_failure": "abort"
                },
                "launch_vscode": {
                    "type": "action",
                    "controller": "launch_app",
                    "args": {"app": "vscode"},
                    "on_success": "done",
                    "on_failure": "abort"
                },
                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": "Workspace setup failed"
                }
            }
        }
    }


@template(name="setup_video_player", params={"folder_name"})
def setup_video_player(folder_name: str="movies") -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "setup_video_player",
            "goal": f"Prepare player to watch",
            "description": f"Open player with folder",
            "entry": "open_player",
            "nodes": {
                "open_player": {
                    "type": "action",
                    "controller": "open_app",
                    "args": {"app_name": "vlc", "folder_name": folder_name},
                    "retries": 1,
                    "on_success": "done",
                    "on_failure": "abort"
                },
                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": f"{folder_name} player setup failed"
                }
            }
        }
    }

@template(name="open_copied_path")
def open_copied_path() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "open_copied_path",
            "goal": "Open explorer in the path from clipboard",
            "description": "Open explorer with path from clipboard",
            "entry_point": "get_copied_value",
            "nodes": {
                "open_path": {
                    "type": "action",
                    "controller": "open_copied_path",
                    "on_success": "done",
                    "on_failure": "abort",
                }
            }
        }
    }


@template(name="open_terminal_here")
def open_terminal_here() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "open_terminal_here",
            "goal": "Open terminal in active project",
            "entry": "get_active_instance",
            "nodes": {
                "get_active_instance": {
                    "type": "action",
                    "controller": "get_active_instance",
                    "output": "active_instance",
                    "on_success": "get_project_name",
                    "on_failure": "abort"
                },

                "get_project_name": {
                    "type": "action",
                    "controller": "get_folder_name",
                    "args": {"instance": "@active_instance"},
                    "output": "project_name",
                    "on_success": "build_project_path",
                    "on_failure": "abort"
                },

                "build_project_path": {
                    "type": "action",
                    "controller": "build_path",
                    "args": {
                        "parent_name": "projects",
                        "folder": "@project_name"
                    },
                    "output": "project_path",
                    "on_success": "open_terminal",
                    "on_failure": "abort"
                },

                "open_terminal": {
                    "type": "action",
                    "controller": "open_app",
                    "args": {
                        "app_name": "cmd",
                        "folder_path": "@project_path"
                    },
                    "on_success": "done",
                    "on_failure": "abort"
                },

                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": "Failed to open terminal"
                }
            }
        }
    }


@template(name="start_project")
def start_project() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "start_project",
            "goal": "Open a project workspace",
            "entry": "list_projects",
            "nodes": {
                "list_projects": {
                    "type": "action",
                    "controller": "list_folder_contents",
                    "args": {"folder_name": "projects"},
                    "fetch": "folders",
                    "output": "project_folders",
                    "on_success": "select_project",
                    "on_failure": "abort"
                },

                "select_project": {
                    "type": "function",
                    "controller": "fuzzy_select",
                    "args": {
                        "query": "@user_input",
                        "choices": "@project_folders"
                    },
                    "output": "project_name",
                    "on_success": "build_project_path",
                    "on_failure": "abort"
                },

                "build_project_path": {
                    "type": "function",
                    "controller": "build_path",
                    "args": {
                        "parent_name": "projects",
                        "folder": "@project_name"
                    },
                    "output": "project_path",
                    "on_success": "focus_explorer",
                    "on_failure": "abort"
                },

                "focus_explorer": {
                    "type": "action",
                    "controller": "focus_app",
                    "args": {
                        "app_name": "explorer",
                        "query": "@project_name"
                    },
                    "on_success": "open_vscode",
                    "on_failure": "open_explorer"
                },

                "open_explorer": {
                    "type": "action",
                    "controller": "open_folder",
                    "args": {
                        "folder_path": "@project_path"
                    },
                    "on_success": "open_vscode",
                    "on_failure": "abort"
                },

                "open_vscode": {
                    "type": "action",
                    "controller": "open_focus_app",
                    "args": {
                        "app_name": "vscode",
                        "query": "@project_name",
                        "folder_path": "@project_path"
                    },
                    "on_success": "done",
                    "on_failure": "abort"
                },

                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": "Failed to start project"
                }
            }
        }
    }


@template(name="organize_folder")
def organize_folder() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "organize_folder",
            "goal": "Organize files in a folder",
            "entry": "list_items",
            "nodes": {
                "list_items": {
                    "type": "action",
                    "controller": "list_folder_contents",
                    "args": {"folder_name": "@target_folder"},
                    "output": "items",
                    "on_success": "categorize",
                    "on_failure": "abort"
                },

                "categorize": {
                    "type": "action",
                    "controller": "categorize_files",
                    "args": {"files": "@items"},
                    "output": "categorized",
                    "on_success": "move_files",
                    "on_failure": "abort"
                },

                "move_files": {
                    "type": "action",
                    "controller": "batch_move",
                    "args": {"mapping": "@categorized"},
                    "on_success": "done",
                    "on_failure": "abort"
                },

                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": "Folder organization failed"
                }
            }
        }
    }


@template(name="open_copied_path")
def open_copied_path() -> dict:
    return {
        "version": 1.0,
        "task_graph": {
            "id": "open_copied_path",
            "goal": "Open copied file or folder",
            "entry": "get_copied_path",
            "nodes": {
                "get_copied_path": {
                    "type": "action",
                    "controller": "get_copied_value",
                    "args": {"_as": "path"},
                    "output": "file_path",
                    "on_success": "open_location",
                    "on_failure": "abort"
                },

                "open_location": {
                    "type": "action",
                    "controller": "open_folder",
                    "args": {
                        "folder_path": "@file_path::folder",
                        "select_file": "@file_path::file"
                    },
                    "on_success": "done",
                    "on_failure": "abort"
                },

                "done": {"type": "noop"},
                "abort": {
                    "type": "abort",
                    "reason": "Invalid copied path"
                }
            }
        }
    }

