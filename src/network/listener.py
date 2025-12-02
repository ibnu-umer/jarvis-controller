from flask import Flask, request, jsonify
from ..system.system_controller import SystemController



app = Flask(__name__)
sc = SystemController()

@app.route("/action/<name>", methods=["POST"])
def run_action(name):
    params = request.json or {}
    action_func = getattr(sc, name, None)
    if not action_func:
        return jsonify({"error": "Action not found"}), 404
    result = action_func(**params)
    return jsonify(result)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
