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


@app.route('/join', methods=['GET'])
def get_join():
    return render_template('join.html')
 
@app.route('/join', methods=['POST'])
def post_join():
    # 1. 클라이언트로부터 데이터를 받기
    userID_receive = request.form['userID_give']  # 클라이언트로부터 url을 받는 부분
    pw_receive = request.form['pw_give']  # 클라이언트로부터 comment를 받는 부분
    pw2_receive = request.form['pw2_give']  # 클라이언트로부터 comment를 받는 부분
    area_receive = request.form['area_give']  # 클라이언트로부터 comment를 받는 부분
    goingToOffice_receive = request.form['goingToOffice_give']
    goingToOffice_receive2 = goingToOffice_receive[0:2]
    goingHome_receive = request.form['goingHome_give']
    goingHome_receive2 = goingHome_receive[0:2]

    join = {'userID': userID_receive, 'pw': pw_receive, 'pw2': pw2_receive,'area': area_receive, 'goingToOffice': goingToOffice_receive2, 'goingHome': goingHome_receive2}

    db.dbweather.insert_one(join)

    return jsonify({'result': 'success'})

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