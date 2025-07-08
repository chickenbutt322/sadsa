# Google OAuth authentication blueprint for CodeCraft Studio

import json
import os
import requests
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient
from models import User, db

# Environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Replit deployment URL
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost")}/google_login/callback'

# Display setup instructions
print(f"""
=== Google OAuth Setup Instructions ===
To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

# Create blueprint
google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def google_login():
    """Initiate Google OAuth flow"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured. Please check your environment variables.", "error")
        return redirect(url_for("login"))
    
    # Get Google's authorization endpoint
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Create authorization URL
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
        scope=["openid", "email", "profile"],
    )
    
    return redirect(request_uri)


@google_auth.route("/google_login/callback")
def google_callback():
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured.", "error")
        return redirect(url_for("login"))
    
    # Get authorization code
    code = request.args.get("code")
    if not code:
        flash("Authorization failed. Please try again.", "error")
        return redirect(url_for("login"))
    
    try:
        # Get Google's token endpoint
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Exchange code for tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        userinfo = userinfo_response.json()
        
        # Verify email is available and verified
        if not userinfo.get("email_verified"):
            flash("Email not verified by Google. Please use a verified Google account.", "error")
            return redirect(url_for("login"))
        
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", userinfo.get("name", "User"))
        
        # Check if user exists
        user = User.query.filter_by(email=users_email).first()
        
        if not user:
            # Create new user
            user = User(
                username=users_name,
                email=users_email,
                email_verified=True,  # Google accounts are already verified
                password_hash=""  # No password needed for OAuth users
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome to CodeCraft Studio, {users_name}! Your account has been created.", "success")
        else:
            # Update existing user if needed
            if not user.email_verified:
                user.email_verified = True
                db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
        
        # Log in the user
        login_user(user)
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("login"))


@google_auth.route("/logout")
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))