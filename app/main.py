import os
import time
from urllib.parse import quote_plus
from flask import Flask, jsonify
from dotenv import load_dotenv
from app.extensions import db
from app.routes.tickets import tickets_bp
from prometheus_flask_exporter import PrometheusMetrics


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.update(test_config)
    else:
        db_user = os.getenv("POSTGRES_USER")
        db_password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
        db_name = os.getenv("POSTGRES_DB")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_host = os.getenv("DB_HOST", "localhost")

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(tickets_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "devops-ticketing-lab"}), 200
    @app.route("/simulate/slow", methods=["GET"])
    def simulate_slow_response():
        time.sleep(1)
        return {"status": "slow response simulated"}, 200

    with app.app_context():
        db.create_all()

    if not app.config.get("TESTING"):
        metrics = PrometheusMetrics(app)
        metrics.info(
            "app_info", 
            "Ticketing Lab application info", 
            version="1.0.0"
        )

    return app


if __name__ == "__main__":
    app = create_app()
    print("=== REGISTERED ROUTES ===")
    print(app.url_map)
    print("==========================")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)