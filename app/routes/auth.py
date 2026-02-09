from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required

# Import the service that automatically switches between Mock and AWS
from app.config_services import users_service

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.signup'))

        # Create user returns a tuple: (user_object, error_message)
        user, error = users_service.create_user(email, username, password)

        if user:
            login_user(user)
            # --- FIX 1: Enforce the 7-Day Session from Config ---
            session.permanent = True 
            flash('Account created successfully!', 'success')
            return redirect(url_for('web.gallery')) # Redirect to gallery instead of home
        else:
            flash(error, 'error')

    # --- FIX 2: Standardized Template Path (Removed 'auth/' prefix) ---
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # We can still use the checkbox, but we force permanent session below
        remember = True if request.form.get('remember') else False

        user, error = users_service.validate_login(email, password)

        if user:
            login_user(user, remember=remember)
            
            # --- FIX 1: Enforce the 7-Day Session from Config ---
            # Without this line, PERMANENT_SESSION_LIFETIME in config.py is IGNORED.
            session.permanent = True 
            
            return redirect(url_for('web.gallery'))
        else:
            flash(error, 'error') 
            
    # --- FIX 2: Standardized Template Path ---
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))