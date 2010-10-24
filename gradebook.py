import sqlite3
from flask import Flask, g, url_for, redirect, render_template

DATABASE = "./gradebook.db"
DEBUG = True
SECRET_KEY = "'K\xaf\xd2\xc7\xc2#J\x05s%\x99J\x8e\xda\x85\xbe<t\xb2\xea\xab\xa7\xa4\xef'"

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    """Return a connection to the gradebook database"""
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/')
def index():
    return redirect(url_for("gradebook"), code=302)

@app.route('/gradebook/')
def gradebook():
    return render_template("gradebook.html")


if __name__ == '__main__':
    app.run()
