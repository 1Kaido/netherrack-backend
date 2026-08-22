import os
from flask import Blueprint, redirect, url_for
from flask_jwt_extended import create_access_token  # pyright: ignore[reportMissingImports]

from extensions import google
from models import User, db


auth_bp = Blueprint("auth", __name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")


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

        user = User(
            google_id=google_id,
            email=email
        )

        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(
        identity=str(user.id)
    )

    return redirect(f"{FRONTEND_URL}/callback.html?token={access_token}")