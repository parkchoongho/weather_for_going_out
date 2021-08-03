from flask import Flask, render_template, jsonify, request, make_response, redirect, url_for
from pymongo import MongoClient
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('localhost', 27017)
db = client.dbweather

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    if cookie_check():
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def post_login():
    userId = request.form['user_id']
    password = request.form['password']
    user = db.users.find_one({'userId' : userId, 'password': password}, {'password' : False})
    resp = make_response(jsonify({'result':'success', 'msg':'POST 연결되었습니다!'}))
    resp.set_cookie(key='userId', value=user['userId'], httponly=True)
    resp.set_cookie(key='auth', value=bcrypt.generate_password_hash(user['userId'] + password), httponly=True)
    return resp

def cookie_check():
    user_id_cookie = request.cookies.get('userId')
    auth_cookie = request.cookies.get('auth')
    if user_id_cookie is not None and auth_cookie is not None:
        user = db.users.find_one({'userId' : user_id_cookie})
        is_auth_right = bcrypt.check_password_hash(auth_cookie, user_id_cookie + user['password'])
        return is_auth_right
   
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)