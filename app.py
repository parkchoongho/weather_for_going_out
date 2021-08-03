from flask import Flask, render_template, jsonify, request, make_response
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbweather

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    user_id = request.cookies.get('userId')
    print(user_id)
    # print(request.headers.get('Cookie', type=str))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def post_login():
    userId = request.form['user_id']
    password = request.form['password']
    user = db.users.find_one({'userId' : userId, 'password': password}, {'password' : False})
    resp = make_response(jsonify({'result':'success', 'msg':'POST 연결되었습니다!'}))
    resp.set_cookie(key='userId', value=user['userId'], httponly=True)
    return resp

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)