import sys
from pathlib import Path
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.models import User, db
from sqlalchemy import or_

# Add backend directory to system path for imports
sys.path.append(str(Path(__file__).parents[1]))

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.user_dashboard'))

        if request.method == 'GET':
            return render_template('login.html')

        # Handle POST data from form or JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            flash("Please fill in all fields", "danger")
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            if hasattr(user, 'update_last_login'):
                user.update_last_login()
                db.session.commit()
            logger.info(f'Successful login for user {username}')
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.user_dashboard'))
        else:
            logger.warning(f'Failed login attempt for user {username}')
            flash("Invalid username or password", "danger")
            return render_template('login.html')

    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        flash("An error occurred during login. Please try again.", "danger")
        db.session.rollback()
        return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.user_dashboard'))

        if request.method == 'GET':
            return render_template('register.html')

        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not username or not email or not password:
            flash("Please fill in all fields", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long", "danger")
            return render_template('register.html')

        user_exists = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()

        if user_exists:
            msg = 'Username already exists' if user_exists.username == username else 'Email already registered'
            flash(msg, "danger")
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        logger.info(f'New user registered: {username}')
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'Registration failed: {str(e)}')
        flash("Registration failed. Please try again.", "danger")
        return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'fitbit_connected': getattr(current_user, 'fitbit_connected', False)
    })
