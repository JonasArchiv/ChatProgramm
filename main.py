import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime
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


if __name__ == '__main__':
    app.run(debug=True, port=5600)
