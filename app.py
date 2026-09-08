from dotenv import load_dotenv
load_dotenv()
from datetime import date
from datetime import timedelta
import os
import json
import queue
from threading import Thread
from flask import (Flask,request,jsonify,Response,stream_with_context)
from flask_cors import CORS
from flask_jwt_extended import (JWTManager,jwt_required,get_jwt_identity)
from routes.auth_routes import auth_bp
from sse.routes import sse_bp
from extensions import oauth
from models import db
from agent import (
    create_researcher_on_tier
)

app = Flask(__name__)

#CONFIGS
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True,"pool_recycle": 300,}
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['JWT_TOKEN_LOCATION'] = ['cookies'] 
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'None'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)


db.init_app(app)
CORS(app, supports_credentials=True)
jwt = JWTManager(app)
oauth.init_app(app)

#BLUEPRINTS
app.register_blueprint(auth_bp)
app.register_blueprint(sse_bp, url_prefix="/api")
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
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt")
    tier = data.get("tier", "stone")
    print("tier is: " + str(tier))
    if not prompt:
        return jsonify({
            "success": False,
            "error": "No prompt sent"
        }), 400
    
    today = date.today()
    researcher = create_researcher_on_tier(tier)
    result = researcher(
    f"""
    Today's date is {today}.
    User's task:
    {prompt}
    """
    )
    return jsonify({
        "success": True,
        "result": result
    }), 200
        

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
