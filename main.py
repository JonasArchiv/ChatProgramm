import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = 'secret_salt'  # Change this on Public build!
db = SQLAlchemy(app)

app_name = 'App-Name'  # Change this to your App-Name


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    vorname = db.Column(db.String(80), nullable=False)
    nachname = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(180), nullable=False)
    isAdmin = db.Column(db.Boolean, default=False)
    isCompany = db.Column(db.Boolean, default=False)
    account_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow())


class MessageChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.String(10000), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.datetime.utcnow())


def check_permissions(required_permissions):
    if 'username' not in session:
        return False
    session_user = db.session.get(User, session['user_id'])
    for permission in required_permissions:
        if not getattr(session_user, permission):
            return False
    return True


if not os.path.exists('instance/db.db'):
    with app.app_context():
        db.create_all()
        print("Datenbank erstellt.")


@app.route('/')
def index():
    return render_template('index.html', app_name=app_name)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', app_name=app_name, user_name=session.username)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        nname = request.form['nname']
        vname = request.form['vname']
        username = request.form['username']
        raw_password = request.form['password']
        hash_password = generate_password_hash(raw_password)

        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_username = User.query.filter_by(username=username).first()

        if existing_user_email or existing_user_username:
            flash('Email or Username already exists. Please choose a different Email or Username', 'error')
            return redirect(url_for('register'))

        user = User(email=email, vorname=vname, nachname=nname, username=username, password=hash_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login', success='Account created successfully. Please login.'))
    return render_template('register.html', error=request.args.get('error'), success=request.args.get('success'),
                           app_name=app_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id

        return redirect(url_for('login', error='Invalid username or password'))
    return render_template('login.html', error=request.args.get('error'), success=request.args.get('success'),
                           app_name=app_name)


@app.route('/logout')
def logout():
    if 'user_id' not in session:
        return redirect(url_for('login', error='You are not logged in'))
    session.pop('user_id', None)
    session.pop('private_key', None)
    return redirect(url_for('login', success='You have logged out successfully.'))


@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login', error='You are not logged in'))

    user_id_current = session.get('user_id')
    user_current = User.query.get(user_id_current)

    user_partner = User.query.get(user_id)

    if not user_partner:
        return redirect(url_for('index', error='User not found'))

    if request.method == 'POST':
        message_text = request.form['message']

        message = MessageChat(sender_id=user_id_current, receiver_id=user_id, text=message_text)
        db.session.add(message)
        db.session.commit()

    messages = MessageChat.query.filter(
        ((MessageChat.sender_id == user_id_current) & (MessageChat.receiver_id == user_id)) |
        ((MessageChat.sender_id == user_id) & (MessageChat.receiver_id == user_id_current))
    ).order_by(MessageChat.created_at)

    return render_template('chat.html', user_partner=user_partner, messages=messages, app_name=app_name)


if __name__ == '__main__':
    app.run(debug=True, port=5600)
