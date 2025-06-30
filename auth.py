from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        print(f"[LOGIN DEBUG] Tentativo login - Username: '{username}', Password length: {len(password)}")
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"[LOGIN DEBUG] Utente trovato: {user.username}")
            password_valid = check_password_hash(user.password_hash, password)
            print(f"[LOGIN DEBUG] Password valida: {password_valid}")
            
            if password_valid:
                login_user(user)
                print(f"[LOGIN DEBUG] Login riuscito per: {username}")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
            else:
                print(f"[LOGIN DEBUG] Password errata per: {username}")
                flash('Password errata', 'error')
        else:
            print(f"[LOGIN DEBUG] Utente non trovato: {username}")
            flash('Nome utente non trovato', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
