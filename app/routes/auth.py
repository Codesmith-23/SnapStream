from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

# --- THE FIX IS HERE ---
# 1. Import the service that automatically switches between Mock and AWS
from app.config_services import users_service

# 2. DELETE the lines that initialized MockUsers manually.
#    (We do not need os, BASE_DIR, or MOCK_DIR here anymore)

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
            flash('Account created successfully!', 'success')
            return redirect(url_for('web.gallery'))
        else:
            flash(error, 'error')

    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Validate returns a tuple: (user_object, error_message)
        user, error = users_service.validate_login(email, password)

        if user:
            login_user(user, remember=remember)
            return redirect(url_for('web.gallery'))
        else:
            # This handles "Invalid format", "Not found", and "Wrong password"
            flash(error, 'error') 
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))