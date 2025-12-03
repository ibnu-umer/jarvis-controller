from flask import Flask, request, jsonify
import threading
import requests
from configs.config import WIN_HOST, WIN_PORT
from core.registry import MODULE_REGISTRY, FUNCTION_REGISTRY




class WindowsListener:
    def __init__(self, host=WIN_HOST, port=WIN_PORT):
        self.host = host
        self.port = port
        self.app = Flask("WindowsListener")
        self.server_thread = None
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
                result = action_func(**params)
                return jsonify({
                    "status": "success",
                    "action": name,
                    "result": result
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

           
        

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


    def stop(self):
        try:
            requests.get(f"http://{self.host}:{self.port}/shutdown")
        except Exception:
            pass
        print("Stop requested for Windows listener thread (Flask will exit).")
        if self.server_thread:
            self.server_thread.join(timeout=2)
            self.server_thread = None