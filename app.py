from dotenv import load_dotenv  # type: ignore[reportMissingImports]
load_dotenv()

from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS  # type: ignore[reportMissingImports]
from flask_jwt_extended import (  # type: ignore[reportMissingImports]
    JWTManager,
    jwt_required,
    get_jwt_identity,
)
from routes.auth_routes import auth_bp
from extensions import oauth
from models import db
#from agent import researcher
import os


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
CORS(app)

db.init_app(app)
jwt = JWTManager(app)
oauth.init_app(app)
app.register_blueprint(auth_bp)


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to the Researcher API",
        "status": "success"
    }), 200

@app.route("/research", methods=["POST"])
@jwt_required()
def user_prompt():
    user_id = get_jwt_identity()
    data = request.json
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({
            "success": False,
            "error": "No prompt sent"
        }), 400

    print("User:", user_id)
    print("Prompt:", prompt)

    today = date.today().strftime("%B %d, %Y")
   # result = researcher(f"Today's date is {today} your task is {prompt}")

    return jsonify({
        "success": True
       # "result": str(result)
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )