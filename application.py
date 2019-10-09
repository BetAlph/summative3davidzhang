'''
If running from Mac, run this command first!

export FLASK_APP="application.py" DATABASE_URL="postgres://wvenojhujcidrk:db3cff2e367514a94dff20e895be599f419c7c92bf5e907f2358e4f8ff7f78f3@ec2-54-163-226-238.compute-1.amazonaws.com:5432/d6k656cqrila1b" FLASK_DEBUG=1


posts = [
{
'year': 'Corey Schafer',
'title': 'Blog Post 1',
'imdbid': 'First post content',
'imdbrating': 'April 20, 2018'
},
{
'year': 'Corey Schafer',
'title': 'Blog Post 1',
'imdbid': 'First post content',
'imdbrating': 'April 20, 2018'
}
]

'''

import os

from flask import Flask, render_template, request
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager,login_user, current_user, logout_user, login_required



app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/")
def index():
    return render_template("index.html")
