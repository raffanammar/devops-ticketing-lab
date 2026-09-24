from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/alerts", methods=["POST"])
def receive_alert():
    payload = request.get_json()

    print("=== ALERT RECEIVED ===", flush=True)
    print(payload, flush=True)
    print("======================", flush=True)

    return jsonify({"status": "received"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)