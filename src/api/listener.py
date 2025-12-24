from flask import Flask, request, jsonify
import threading, requests, inspect, asyncio
from configs.config import WIN_HOST, WIN_PORT
from core.registry import MODULE_REGISTRY, FUNCTION_REGISTRY, file_registry
from core.logger import logger




class WindowsListener:
    def __init__(self, host=WIN_HOST, port=WIN_PORT):
        self.host = host
        self.port = port
        self.app = Flask("WindowsListener")
        self.server_thread = None
        self.tray = None
        self._setup_routes()


    def _setup_routes(self):
        @self.app.route("/action/<name>", methods=["POST"])
        def handle_action(name):
            func_info = FUNCTION_REGISTRY.get(name)
            if not func_info:
                return jsonify({"error": f"Unknown action: {name}"}), 404

            instance = MODULE_REGISTRY.get(func_info["class"])
            if not instance:
                return jsonify({"error": f"No module instance for class {func_info['class']}"}), 500

            action_func = getattr(instance, func_info["function"], None)
            if not callable(action_func):
                return jsonify({"error": f"Function not found: {func_info['function']}"}), 500

            params = request.json or {}

            try:
                if inspect.iscoroutinefunction(action_func):
                    res = asyncio.run(action_func(**params))
                else:
                    res = action_func(**params)

                logger.info(res)
                return jsonify({
                    "status": "success",
                    "action": name,
                    "result": res
                })

            except Exception as e:
                logger.info({"error": str(e)})
                return jsonify({"error": str(e)}), 500


        @self.app.route("/registry", methods=["GET"])
        def registry():
            modules_registry = {
                name: {
                    "module": meta.get("module"),
                    "class": meta.get("class"),
                    "function": meta.get("function"),
                    "params": list(meta.get("params", [])) # convert params to list, because set cannot json encode
                }
                for name, meta in FUNCTION_REGISTRY.items()
            }

            file_registry_dict = file_registry.get_registered_files()
            return jsonify({
                "modules_registry": modules_registry,
                "file_registry": file_registry_dict
            }), 200
        

        @self.app.route("/progress", methods=["POST"])
        def log_progress():
            data = request.get_json(force=True)
            action = data.get("action")
            status = data.get("status")

            if not action or not status:
                return jsonify({"error": "Missing action or status"}), 400
            
            self.tray.popup.log_progress(action, status)
            logger.info(f"action: {action}, status: {status}")
            return jsonify({"ok": True}), 200
        

        @self.app.route("/shutdown", methods=["GET"])
        def shutdown():
            func = request.environ.get('werkzeug.server.shutdown')
            if func:
                func()
                return "Server shutting down..."
            return "Unable to shutdown", 500
        

    def _run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)


    def start(self):
        if not self.server_thread:
            self.server_thread = threading.Thread(target=self._run, daemon=True)
            self.server_thread.start()
            print(f"Windows listener running at http://{self.host}:{self.port} in background thread...")
            logger.info(f"Windows listener running at http://{self.host}:{self.port} in background thread...")


    def stop(self):
        try:
            requests.get(f"http://{self.host}:{self.port}/shutdown")
        except Exception:
            pass
        print("Stop requested for Windows listener thread (Flask will exit).")
        if self.server_thread:
            self.server_thread.join(timeout=2)
            self.server_thread = None



    