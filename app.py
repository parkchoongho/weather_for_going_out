from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from pymongo import MongoClient
# from bson.objectid import ObjectId
import datetime  # 날짜시간모듈
from datetime import date, datetime, timedelta  # 현재 날짜 외의 날짜 구하기 위한 모듈
import requests
import json  # json 파일 파싱하여 데이터 읽는 모듈
from flask_bcrypt import Bcrypt
from flask_session import Session

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'sdkmcslkcmks'

client = MongoClient('localhost', 27017)
db = client.dbweather

# @app.route('/', methods=['GET'])
# def home():
#     return render_template('index.html')

@app.route('/')
def main():
    # session있는지 확인 없으면 로그인화면으로 리다이렉트
    if session_check() == False:
        return redirect(url_for('login'))

    # 기상청 단기예보 조회서비스 api 데이터 url 주소
    weather_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?"

    # 발급 받은 인증키(Encoding)
    service_key = "pZ8v2mCXxDSt%2FQI%2FQDevXC2qiy5pgglRf5f%2BYAUilg2ijTpqIig8oKvFyqUT5pkMrdNMZ1WuhJ6AdKymzBrsmQ%3D%3D"

    now = datetime.now()
    
    # 어제
    yesterday = date.today() - timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y%m%d')

    # 오늘
    today = datetime.today()  # 현재 지역 날짜 반환
    today_date = today.strftime("%Y%m%d")  # 오늘의 날짜 (연도/월/일 반환)

    # 내일
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%Y%m%d')

    # 하루에 8번 데이터 업데이트 됨. (0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300)
    # api를 가져오려는 시점의 이전 발표시각에 업데이트된 데이터를 base_time, base_date로 설정
    if now.hour < 2 or (now.hour == 2 and now.minute <= 10): # 0시~2시 10분
        base_date = yesterday_date  # 발표날짜가 어제
        base_time = "2300"
    elif now.hour < 5 or (now.hour == 5 and now.minute <= 10):  # 2시 11분~5시 10분
        base_date = today_date
        base_time = "0200"
    elif now.hour < 8 or (now.hour == 8 and now.minute <= 10):  # 5시 11분~8시 10분
        base_date = today_date
        base_time = "0500"
    elif now.hour < 11 or (now.hour == 11 and now.minute <= 10):  # 8시 11분~11시 10분
        base_date = today_date
        base_time = "0800"
    elif now.hour < 14 or (now.hour == 14 and now.minute <= 10):  # 11시 11분~14시 10분
        base_date = today_date
        base_time = "1100"
    elif now.hour < 17 or (now.hour == 17 and now.minute <= 10):  # 14시 11분~17시 10분
        base_date = today_date
        base_time = "1400"
    elif now.hour < 20 or (now.hour == 20 and now.minute <= 10):  # 17시 11분~20시 10분
        base_date = today_date
        base_time = "1700" 
    elif now.hour < 23 or (now.hour == 23 and now.minute <= 10):  # 20시 11분~23시 10분
        base_date = today_date
        base_time = "2000"
    else:  # 23시 11분 ~ 23시 59분
        base_date = today_date
        base_time = "2300"

    # 날짜, 예보시각, 위경도 정보 받아오는 변수로 수정해야 함.
    payload = "serviceKey=" + service_key + "&" +\
        "pageNo=" + '1' + '&' +\
        "numOfRows=" + '270' + '&' +\
        "dataType=json" + "&" +\
        "base_date=" + base_date + "&" +\
        "base_time=" + base_time + "&" +\
        "nx=" + "62" + "&" +\
        "ny=" + "120"

    print(payload)
    
    res = requests.get(weather_url + payload)
    items = res.json().get('response').get('body').get('items')
    # print(items)

    

    return render_template('index.html')


@app.route('/update', methods=['POST'])
def update_user():
    userID = request.form['uesrID']
    pw = request.form['pw']
    pw2 = request.form['pw2']
    area = request.form['area']
    goingToOffice = request.form['goingToOffice']
    goingHome = request.form['goingHome']

    db.users.update_one({'userID': userID}, {
                        '$set': {'pw': pw,
                                 'pw2': pw2,
                                 'area': area,
                                 'goingToOffice': goingToOffice,
                                 'goingHome': goingHome}})

@app.route('/join', methods=['GET'])
def get_join():
    all_sido = list(db.grid.find({}))
    print(all_sido)
    return render_template('join.html', all_sido=all_sido)

@app.route('/join', methods=['POST'])
def post_join():
    # 1. 클라이언트로부터 데이터를 받기
    userID_receive = request.form['userID_give'] 
    pw_receive = request.form['pw_give'] 
    pw2_receive = request.form['pw2_give']
    area_receive = request.form['area_give'] 
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
        return redirect(url_for('main'))
    if session_check():
        return redirect(url_for('main'))
    return render_template('login.html')

def session_check():
    userId = session.get('userId')
    if userId is None:
        return False
    return True

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)