import os
from flask import Blueprint, redirect, url_for
from flask_jwt_extended import create_access_token  
from extensions import google
from models import User, db
from flask import Flask, jsonify, request
from flask_jwt_extended import(
    JWTManager, create_access_token, create_refresh_token,jwt_required,get_jwt_identity,set_refresh_cookies,unset_jwt_cookies
)
from datetime import timedelta
from flask_cors import CORS
import datetime
from flask_jwt_extended import set_access_cookies
from datetime import timedelta

app = Flask(__name__)
CORS(app, supports_credentials=True) 
auth_bp = Blueprint("auth", __name__)
#FRONTEND_URL = os.getenv("FRONTEND_URL", "https://thenetherrack.vercel.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5000")
@auth_bp.route("/auth/google")
def google_login():
    redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )
    return google.authorize_redirect(
        redirect_uri
    )

@auth_bp.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    userinfo = token["userinfo"]
    google_id = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name")
    user = User.query.filter_by(
        google_id=google_id
    ).first()
    if not user:
        user = User(google_id=google_id,email=email)
        db.session.add(user)
        db.session.commit()

        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        response = jsonify({
            'message':'login done'
        })
        #set cookies
        set_access_cookies(response,access_token)
        set_refresh_cookies(response,refresh_token)
        return response
    
    return jsonify({
        "message":"login done"
    })

@app.route('/refresh')
@jwt_required(refresh=True)
def refresh_token():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    response = jsonify({
        "message": "Token refreshed"
    })
    set_refresh_cookies(response,new_access_token)


