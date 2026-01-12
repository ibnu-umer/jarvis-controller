from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from rapidfuzz import process
from pathlib import Path
import os



@dataclass
class ExecutionResult:
    graph_id: str
    status: str                 # "success" | "failure"
    executed_nodes: List[str]
    failed_node: Optional[str]
    message: Optional[str]
    error: Optional[str]
    context: Dict[str, Any]


class Executor:
    def __init__(self, controller_client, state_provider, file_registry):
        self.controller = controller_client
        self.state = state_provider
        self.file_registry = file_registry

    async def execute(self, user_input: str, plan) -> ExecutionResult:
        return  await self._execute_graph(user_input, plan)

    async def _execute_action(self, user_input, action) -> ExecutionResult:
        res = await self.controller.trigger(action.action, action.params)
        status = res["result"]["status"]
        await self.controller.log_progress(
            user_input, action.action, action.action, status
        )
        return res


    async def _execute_graph(self, user_input, graph) -> ExecutionResult:
        tg = graph["task_graph"]
        nodes = tg["nodes"]
        current = tg["entry"]

        executed: List[str] = []
        context: Dict[str, Any] = {"user_input": user_input}
        
        if tg["id"] == "fallback":
            return self._failure(
                tg["id"],
                executed,
                current,
                "Cannot understand",
                context
            )

        try:
            while True:
                if current not in nodes:
                    raise RuntimeError(f"Unknown node: {current}")

                node = nodes[current]
                executed.append(current)

                node_type = node["type"]

                # --- NOOP ---
                if node_type == "noop":
                    return self._success(tg["id"], executed, context)

                # --- ABORT ---
                if node_type == "abort":
                    return self._failure(
                        tg["id"],
                        executed,
                        current,
                        node.get("reason", "Aborted"),
                        context
                    )

                # --- DECISION ---
                if node_type == "decision":
                    status = context[node["condition"]]
                    current = node["on_true"] if status else node["on_false"]
                    continue

                # --- ACTION ---
                if node_type == "action":
                    retries = node.get("retries", 0)
                    output_key = node.get("output")
                    fetch = node.get("fetch", None)

                    resolved_args = self._resolve_args(
                        node.get("args", {}),
                        context
                    )

                    last_error = None
                    for _ in range(retries + 1):
                        response = await self.controller.trigger(
                            action=node["controller"],
                            params=resolved_args
                        )


                        if not isinstance(response, dict):
                            raise RuntimeError(
                                f"Controller '{node['controller']}' must return dict"
                            )
                        
                        result = response["result"]
                        if result.get("success"):
                            if output_key:
                                data = result["data"].get(fetch) if fetch else result.get("data")
                                context[output_key] = data
                            context["message"] = result.get("message")
                            current = node["on_success"]
                            break
                        else:
                            last_error = response.get("error")

                    else:
                        current = node["on_failure"]

                    continue
                
                
                if node_type == "function":
                    retries = node.get("retries", 0)
                    output_key = node.get("output")

                    resolved_args = self._resolve_args(
                        node.get("args", {}),
                        context
                    )

                    last_error = None
                    for _ in range(retries + 1):
                        fn = getattr(self, node["controller"])
                        response = fn(**resolved_args)

                        if response:
                            if output_key:
                                context[output_key] = response
                            current = node["on_success"]
                            break
                        else:
                            last_error = response.get("error")

                    else:
                        current = node["on_failure"]

                    continue

                raise RuntimeError(f"Unsupported node type: {node_type}")

        except Exception as e:
            return self._failure(
                tg["id"],
                executed,
                current,
                str(e),
                context
            )

    # ---------------- HELPERS ----------------

    def _resolve_args(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        resolved = {}

        for key, value in args.items():
            if isinstance(value, str) and value.startswith("@"):
                resolved[key] = self._resolve_reference(value, context)
            else:
                resolved[key] = value

        return resolved

    def _resolve_reference(self, ref: str, context: Dict[str, Any]) -> Any:
        """
        @var
        @var::field
        """
        path = ref[1:].split("::")
        value = context.get(path[0])

        if value is None:
            raise RuntimeError(f"Context value not found: {path[0]}")

        for part in path[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                raise RuntimeError(f"Cannot access '{part}' on non-dict value")

        return value

    def _success(self, graph_id, executed, context):
        return ExecutionResult(
            graph_id=graph_id,
            status="success",
            executed_nodes=executed,
            failed_node=None,
            message=context["message"],
            error=None,
            context=context
        )

    def _failure(self, graph_id, executed, failed_node, error, context):
        return ExecutionResult(
            graph_id=graph_id,
            status="failure",
            executed_nodes=executed,
            failed_node=failed_node,
            message=None,
            error=error,
            context=context
        )



    def fuzzy_select(self, query, choices):
        match, score, idx = process.extractOne(query, choices)
        return match

    def build_path(self, parent_name: str = None, folder: str = None, path: str = None) -> str:
        if path:
            path = path.strip()

            # Convert Windows path → WSL accessible
            if ":" in path and "\\" in path:
                # Windows → /mnt/c style
                drive = path[0].lower()
                rest = path[2:].replace("\\", "/")
                wsl_path = f"/mnt/{drive}/{rest}"

                # optional check (works in WSL for both files/folders)
                exists = os.path.exists(wsl_path)

                return wsl_path if exists else path  # fallback to original

            # Already WSL-style path
            if path.startswith("/") and os.path.exists(path):
                return path

            return path


        if parent_name and not folder:
            base = self.file_registry.get(parent_name)
            if not base:
                raise ValueError(f"No base path found for: {parent_name}")
            return str(base)


        if parent_name and folder:
            base = self.file_registry.get(parent_name)
            if not base:
                raise ValueError(f"No base path found for: {parent_name}")

            base_str = str(base)

            # WSL Unix: /mnt/c/projects
            if base_str.startswith("/mnt/"):
                return f"{base_str.rstrip('/')}/{folder}"

            # UNC (Windows path exposed to WSL): \\wsl$
            if base_str.lower().startswith("\\\\wsl$"):
                return f"{base_str.rstrip('\\')}\\{folder}"

            # Windows-style path: C:\projects
            if ":" in base_str:
                win = str(Path(base_str) / folder)
                # Convert to WSL so WSL-side can verify load-it
                drive = win[0].lower()
                rest = win[2:].replace("\\", "/")
                return f"/mnt/{drive}/{rest}"

            raise ValueError(f"Unrecognized path format: {base_str}")

        raise ValueError("Invalid path arguments")

