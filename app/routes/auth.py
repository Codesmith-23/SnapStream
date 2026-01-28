import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('web.gallery'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user_service = current_app.services['users']
        user = user_service.validate_login(email, password)
        
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('web.gallery'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('web.gallery'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username') # Get Username
        password = request.form.get('password')
        
        user_service = current_app.services['users']
        
        # Call the updated create_user function
        user, error = user_service.create_user(email, username, password)
        
        if error:
            flash(error, 'error') # Display "Username taken" or "Email exists"
        else:
            login_user(user)
            flash(f'Welcome, {username}!', 'success')
            logger.info(f'[AUTH] New user registered: {username} ({email})')
            return redirect(url_for('web.gallery'))
            
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))