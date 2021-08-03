from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_session import Session

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'sdkmcslkcmks'

client = MongoClient('localhost', 27017)
db = client.dbweather

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":

        userId = request.form['user_id']
        password = request.form['password']
        user = db.users.find_one({'userId' : userId, 'password': password}, {'password' : False})
        if user is None:
            return redirect(url_for('login'))
        session['userId'] = user['userId']
        return redirect(url_for('home'))
    if session_check():
        return redirect(url_for('home'))
    return render_template('login.html')

def session_check():
    userId = session.get('userId')
    if userId is None:
        return False
    return True

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)