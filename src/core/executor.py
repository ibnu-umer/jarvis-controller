from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import inspect, asyncio
from core.registry import FUNCTION_REGISTRY, module_registry



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

    async def execute(self, user_input: str, plan) -> ExecutionResult:
        return  await self._execute_graph(user_input, plan)

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
                    message = node.get("message") or context.get("message")
                    return self._success(tg["id"], executed, context, message)

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

                    resolved_args = self._resolve_args(
                        node.get("args", {}),
                        context
                    )

                    last_error = None
                    for _ in range(retries + 1):
                        func_name = node["controller"]
                        func_info = FUNCTION_REGISTRY.get(func_name)
                        instance = module_registry.get_module(func_info["class"])
                        action_func = getattr(instance, func_info["function"], None)
      
                        if inspect.iscoroutinefunction(action_func):
                            result = asyncio.run(action_func(**resolved_args))
                        else:
                            result = action_func(**resolved_args)

                        if result.get("success"):
                            data = result.get("data", None)
                            if data:
                                context.update(data)

                            context["message"] = result.get("message")
                            current = node["on_success"]
                            break
                        else:
                            last_error = result.get("error")

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

        for part in path[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                raise RuntimeError(f"Cannot access '{part}' on non-dict value")

        return value

    def _success(self, graph_id, executed, context, message):
        return ExecutionResult(
            graph_id=graph_id,
            status="success",
            executed_nodes=executed,
            failed_node=None,
            message=message,
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


