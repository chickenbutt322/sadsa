import json
import os
import requests
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient
from models import User, db

# env vars
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

google_auth = Blueprint("google_auth", __name__)

@google_auth.route("/google_login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured. Please check your environment variables.", "error")
        return redirect(url_for("login"))
    
    # get auth endpoint from google config
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # build redirect_uri carefully
    redirect_uri = url_for("google_auth.google_callback", _external=True, _scheme="https")
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"]
    )
    
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def google_callback():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured.", "error")
        return redirect(url_for("login"))
    
    code = request.args.get("code")
    if not code:
        flash("Authorization failed. Please try again.", "error")
        return redirect(url_for("login"))
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        redirect_uri = url_for("google_auth.google_callback", _external=True, _scheme="https")
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=redirect_uri,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        userinfo = userinfo_response.json()
        
        if not userinfo.get("email_verified"):
            flash("Email not verified by Google. Please use a verified Google account.", "error")
            return redirect(url_for("login"))
        
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", userinfo.get("name", "User"))
        
        user = User.query.filter_by(email=users_email).first()
        
        if not user:
            user = User(
                username=users_name,
                email=users_email,
                email_verified=True,
                password_hash=""
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome to CodeCraft Studio, {users_name}! Your account has been created.", "success")
        else:
            if not user.email_verified:
                user.email_verified = True
                db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
        
        login_user(user)
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("login"))

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))
