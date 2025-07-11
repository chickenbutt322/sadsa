import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from language_handlers import LanguageHandlerFactory
from flask_wtf.csrf import CSRFProtect
import pyotp
import qrcode
import io
import base64
from google_auth import google_auth

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Init Flask app first
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "your_secret_key_here"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Email configuration with debugging
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# For development - suppress SSL requirement and enable debugging
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_DEBUG'] = True
app.config['TESTING'] = False

# Security
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT") or "your_salt_here"

# CSRF Configuration for Replit
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Disable default CSRF checking
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens

# DB config - try PostgreSQL, fallback to local SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}






GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")


# Init db
from extensions import db
db.init_app(app)

# Init email
mail = Mail(app)
csrf = CSRFProtect()
csrf.init_app(app)

# Init security serializer
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Make session permanent every request
@app.before_request
def make_session_permanent():
    session.permanent = True

    # Run cleanup occasionally (not on every request to avoid performance issues)
    import random
    if random.randint(1, 100) == 1:  # 1% chance per request
        try:
            cleanup_unverified_accounts()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

# Create workspace dir if missing
WORKSPACE_DIR = os.path.join(os.getcwd(), 'workspace')
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# Init language handler factory
language_factory = LanguageHandlerFactory()

# Register Google Auth blueprint
app.register_blueprint(google_auth)

# Initialize database
def init_database():
    try:
        import models  # import models so tables exist
        db.create_all()
        logging.info("Database tables created successfully")
        return True
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False

# ROUTES

@app.route('/')
def index():
    # Initialize database on first request if not already done
    if not hasattr(app, '_db_initialized'):
        with app.app_context():
            app._db_initialized = init_database()

    if current_user.is_authenticated:
        from models import Project
        projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
        return render_template('index.html', user=current_user, projects=projects)
    else:
        return render_template('landing.html')

@app.route('/ide')
def ide():
    # Initialize database on first request if not already done
    if not hasattr(app, '_db_initialized'):
        with app.app_context():
            app._db_initialized = init_database()

    if current_user.is_authenticated:
        from models import Project
        projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
        return render_template('index.html', user=current_user, projects=projects)
    else:
        # Allow unauthenticated users to access the IDE
        return render_template('index.html', user=None, projects=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        from models import User
        from sqlalchemy import text

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        totp_token = request.form.get('totp_token', '').strip()

        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')

        # Use parameterized query to prevent SQL injection
        user = User.query.filter(User.username == username).first()

        if user and user.check_password(password):
            if not user.email_verified:
                flash('Please verify your email before logging in. Check your inbox for verification link.', 'warning')
                return render_template('login.html')

            # Check 2FA if enabled
            #if user.is_2fa_enabled:
            #    if not totp_token:
            #        flash('2FA token is required')
            #        return render_template('login.html', show_2fa=True, username=username)
            #    if not user.verify_totp(totp_token):
            #        flash('Invalid 2FA token')
            #        return render_template('login.html', show_2fa=True, username=username)

            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

    return render_template('login.html')

def cleanup_unverified_accounts():
    """Delete unverified accounts older than 24 hours"""
    from models import User
    from datetime import datetime, timedelta

    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    unverified_users = User.query.filter(
        User.email_verified == False,
        User.created_at < cutoff_time
    ).all()

    for user in unverified_users:
        logging.info(f"Deleting unverified account: {user.username} ({user.email})")
        db.session.delete(user)

    if unverified_users:
        db.session.commit()
        logging.info(f"Deleted {len(unverified_users)} unverified accounts")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        from models import User
        import re

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return render_template('register.html')

        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register.html')

        # Check password strength
        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('Password must contain at least one uppercase letter, one lowercase letter, and one number', 'error')
            return render_template('register.html')

        # Clean up old unverified accounts first
        cleanup_unverified_accounts()

        # Check for existing verified users with same username
        existing_user = User.query.filter(User.username == username).first()
        if existing_user and existing_user.email_verified:
            flash('Username already exists', 'error')
            return render_template('register.html')

        # If unverified user exists with same username, delete it
        if existing_user and not existing_user.email_verified:
            logging.info(f"Deleting existing unverified account with username: {username}")
            db.session.delete(existing_user)
            db.session.commit()

        # Check for existing verified users with same email
        existing_email_user = User.query.filter(User.email == email).first()
        if existing_email_user and existing_email_user.email_verified:
            flash('Email already registered', 'error')
            return render_template('register.html')

        # If unverified user exists with same email, delete it
        if existing_email_user and not existing_email_user.email_verified:
            logging.info(f"Deleting existing unverified account with email: {email}")
            db.session.delete(existing_email_user)
            db.session.commit()

        user = User(username=username, email=email)
        user.set_password(password)
        token = user.generate_email_verification_token()

        db.session.add(user)
        db.session.commit()

        # Send verification email
        send_verification_email(user, token)

        flash('Registration successful! Please check your email to verify your account before logging in. Unverified accounts will be deleted after 24 hours.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def send_verification_email(user, token):
    """Send email verification email"""
    try:
        # Generate verification URL
        verification_url = url_for(
            'verify_email', 
            token=token, 
            _external=True
        )

        print(f"Generated verification URL: {verification_url}")  # Debug print

        # Debug logging
        print(f"DEBUG: Sending email to {user.email}")
        print(f"DEBUG: Username: {user.username}")
        print(f"DEBUG: Verification URL: {verification_url}")

        # Check if email is configured
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logging.warning("Email not configured - skipping email send. Set MAIL_USERNAME and MAIL_PASSWORD environment variables.")
            print(f"DEBUG: Would send verification email to {user.email}")
            print(f"DEBUG: Verification URL would be: {verification_url}")
            return

        # Render email template
        html_body = render_template(
            'email_verification_professional.html',
            username=user.username,
            verification_url=verification_url
        )

        # Also render plain text version
        text_body = render_template(
            'email_verification.txt',
            username=user.username,
            verification_url=verification_url
        )

        # Send email
        msg = Message(
            subject='Verify Your Email - CodeCraft Studio',
            recipients=[user.email],
            html=html_body,
            body=text_body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        # Debug the rendered content
        print(f"DEBUG: Email body contains username: {'username' in msg.body and user.username in msg.body}")
        print(f"DEBUG: Email HTML contains username: {'username' in msg.html and user.username in msg.html}")

        mail.send(msg)
        logging.info(f"Verification email sent successfully to {user.email}")
        print(f"SUCCESS: Email sent to {user.email}")

    except Exception as e:
        logging.error(f"Failed to send verification email: {e}")
        print(f"DEBUG: Email send failed - {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")

def send_password_reset_email(user, token):
    """Send password reset email"""
    try:
        reset_url = url_for('reset_password', token=token, _external=True)
        msg = Message(
            'Password Reset - Code Interpreter',
            recipients=[user.email]
        )
        msg.body = f'''
Hello {user.username},

You requested a password reset for your Code Interpreter account. Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
The Code Interpreter Team
        '''
        msg.html = f'''
<h2>Password Reset Request</h2>
<p>Hello {user.username},</p>
<p>You requested a password reset for your Code Interpreter account. Click the button below to reset your password:</p>
<p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
<p>Or copy and paste this link: {reset_url}</p>
<p>This link will expire in 1 hour.</p>
<p>If you didn't request this reset, please ignore this email.</p>
        '''
        mail.send(msg)
    except Exception as e:
        logging.error(f"Failed to send password reset email: {e}")

@app.route('/verify-email/<token>')
def verify_email(token):
    from models import User

    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('login'))

    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        from models import User

        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')

        user = User.query.filter(User.email == email).first()

        if user:
            token = user.generate_password_reset_token()
            db.session.commit()
            send_password_reset_email(user, token)

        # Always show success message to prevent email enumeration
        flash('If that email address is in our database, you will receive a password reset link shortly.', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    from models import User
    import re

    user = User.query.filter_by(password_reset_token=token).first()

    if not user or not user.verify_password_reset_token(token):
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('reset_password.html', token=token)

        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('Password must contain at least one uppercase letter, one lowercase letter, and one number', 'error')
            return render_template('reset_password.html', token=token)

        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()

        flash('Password reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/about')
def about():
    return render_template('about.html')

# Code execution and project management routes
@app.route('/execute', methods=['POST'])
def execute_code():
    """Execute code in the specified language"""
    try:
        data = request.get_json()
        
        if not data:
            return {'error': 'No data provided'}, 400
        
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        
        if not code:
            return {'error': 'No code provided'}, 400
        
        # Get language handler
        handler = language_factory.get_handler(language)
        if not handler:
            return {'error': f'Language "{language}" not supported'}, 400
        
        # Execute code
        result = handler.execute(code)
        
        # Convert to expected format
        if 'exit_code' in result:
            return {
                'output': result.get('output', ''),
                'error': result.get('error', '') if result.get('exit_code', 0) != 0 else None,
                'execution_time': 0
            }
        else:
            return result
        
    except Exception as e:
        logging.error(f"Error executing code: {e}")
        return {'error': f'Execution failed: {str(e)}'}, 500

@app.route('/save', methods=['POST'])
def save_project():
    """Save code as a project"""
    try:
        data = request.get_json()
        
        if not data:
            return {'error': 'No data provided'}, 400
        
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        name = data.get('name', 'Untitled Project')
        
        if not code:
            return {'error': 'No code provided'}, 400
        
        # If user is authenticated, save to database
        if current_user.is_authenticated:
            from models import Project
            
            # Create new project
            project = Project(
                name=name,
                description=f"Project created in {language}",
                language=language,
                code=code,
                user_id=current_user.id
            )
            
            db.session.add(project)
            db.session.commit()
            
            return {'message': 'Project saved successfully', 'project_id': project.id}
        else:
            # For guest users, just return success (could implement session storage)
            return {'message': 'Code saved locally (login to save permanently)'}
        
    except Exception as e:
        logging.error(f"Error saving project: {e}")
        return {'error': f'Save failed: {str(e)}'}, 500

@app.route('/languages', methods=['GET'])
def get_languages():
    """Get list of supported languages"""
    try:
        languages = []
        for lang in language_factory.get_supported_languages():
            handler = language_factory.get_handler(lang)
            if handler:
                lang_info = handler.get_language_info()
                languages.append(lang_info)
        
        return {'languages': languages}
        
    except Exception as e:
        logging.error(f"Error getting languages: {e}")
        return {'error': f'Failed to get languages: {str(e)}'}, 500

@app.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.email_verified:
        flash('Your email is already verified', 'info')
        return redirect(url_for('index'))

    token = current_user.generate_email_verification_token()
    db.session.commit()
    send_verification_email(current_user, token)

    flash('Verification email sent! Please check your inbox.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/cleanup-unverified')
def admin_cleanup():
    """Admin route to manually trigger cleanup of unverified accounts"""
    # Simple admin check - you might want to add proper admin authentication
    if not current_user.is_authenticated or current_user.username != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    cleanup_unverified_accounts()
    flash('Cleanup completed successfully', 'success')
    return redirect(url_for('index'))

# Removed duplicate routes - using the ones defined above

@app.route('/api/validate', methods=['POST'])
def validate_code():
    """Validate code syntax"""
    try:
        data = request.get_json()
        
        if not data:
            return {'error': 'No data provided'}, 400
        
        code = data.get('code', '').strip()
        language = data.get('language', '').lower()
        
        if not code:
            return {'valid': True, 'message': 'No code to validate'}
        
        if not language:
            return {'error': 'No language specified'}, 400
        
        # Get language handler
        handler = language_factory.get_handler(language)
        if not handler:
            return {'error': f'Unsupported language: {language}'}, 400
        
        # Validate code
        is_valid, message = handler.validate(code)
        
        return {
            'valid': is_valid,
            'message': message or ('Syntax is valid' if is_valid else 'Syntax error')
        }
        
    except Exception as e:
        logging.error(f"Error validating code: {e}")
        return {'error': f'Validation error: {str(e)}'}, 500

# add more routes here like /api/languages, /api/execute, etc.

if __name__ == '__main__':
    # Try port 5000 first, then find an available port
    import socket

    def find_available_port(start_port=5000):
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return start_port

port = int(os.environ.get("PORT", 5000))
print(f"Starting server on port {port}")
app.run(host='0.0.0.0', port=port, debug=True)
