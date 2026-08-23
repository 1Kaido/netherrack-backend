from dotenv import load_dotenv
load_dotenv()

from datetime import date
import os
import json
import queue
from threading import Thread

from flask import (
    Flask,
    request,
    jsonify,
    Response,
    stream_with_context,
)

from flask_cors import CORS

from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)

from routes.auth_routes import auth_bp
from extensions import oauth
from models import db

from agent import (
    researcher,
    create_research,
    status_queues,
    current_research_id,
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL"
)

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY"
)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY"
)


# =========================================================
# EXTENSIONS
# =========================================================

db.init_app(app)

CORS(app)

jwt = JWTManager(app)

oauth.init_app(app)

app.register_blueprint(auth_bp)


# =========================================================
# DATABASE
# =========================================================

with app.app_context():
    db.create_all()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to the Researcher API",
        "status": "success"
    }), 200


# =========================================================
# START RESEARCH
# =========================================================

@app.route("/research", methods=["POST"])
@jwt_required()
def user_prompt():

    user_id = get_jwt_identity()

    data = request.get_json(silent=True) or {}

    prompt = data.get("prompt")

    if not prompt:
        return jsonify({
            "success": False,
            "error": "No prompt sent"
        }), 400

    print("User:", user_id)
    print("Prompt:", prompt)

    # Create a unique queue/session
    research_id = create_research()

    def run_agent():

        # Bind this thread to this research session
        token = current_research_id.set(research_id)

        try:

            today = date.today().strftime(
                "%B %d, %Y"
            )

            result = researcher(
                f"""
Today's date is {today}.

User's task:
{prompt}
"""
            )

            # Get this research's queue
            q = status_queues.get(research_id)

            if q:
                q.put({
                    "type": "done",
                    "stage": "done",
                    "message": "Research completed",
                    "result": str(result)
                })

        except Exception as e:

            print(
                f"Research error [{research_id}]:",
                e
            )

            q = status_queues.get(research_id)

            if q:
                q.put({
                    "type": "error",
                    "stage": "error",
                    "message": str(e)
                })

        finally:

            # Remove ContextVar from this thread
            current_research_id.reset(token)

    # Run agent in background
    Thread(
        target=run_agent,
        daemon=True
    ).start()

    # Immediately return research ID
    return jsonify({
        "success": True,
        "research_id": research_id
    }), 202


# =========================================================
# LIVE STREAM
# =========================================================

@app.route("/research/stream/<research_id>")
@jwt_required()
def research_stream(research_id):

    q = status_queues.get(research_id)

    if q is None:
        return jsonify({
            "success": False,
            "error": "Research session not found"
        }), 404

    def generate():

        while True:

            try:

                event = q.get(
                    timeout=30
                )

                yield (
                    f"data: "
                    f"{json.dumps(event)}"
                    f"\n\n"
                )

                # End stream
                if event.get("type") in (
                    "done",
                    "error"
                ):
                    break

            except queue.Empty:

                # Keep connection alive
                yield ": heartbeat\n\n"

    return Response(
        stream_with_context(
            generate()
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
