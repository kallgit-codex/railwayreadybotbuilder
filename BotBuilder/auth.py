
from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
import os

auth_bp = Blueprint('auth', __name__)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    admin_email = os.getenv('ADMIN_EMAIL')
    admin = Admin.query.first()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # First-time setup
        if admin is None:
            if email != admin_email:
                return "Invalid email for setup", 403
            new_admin = Admin(email=email, password_hash=generate_password_hash(password))
            db.session.add(new_admin)
            db.session.commit()
            session['admin'] = new_admin.email
            return redirect(url_for('dashboard'))

        # Normal login
        if admin and check_password_hash(admin.password_hash, password) and email == admin.email:
            session['admin'] = admin.email
            return redirect(url_for('dashboard'))
        return "Invalid credentials", 403
    return '''
        <form method="post">
            <input type="text" name="email" placeholder="Email"><br>
            <input type="password" name="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
    '''

@auth_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('auth.login'))
