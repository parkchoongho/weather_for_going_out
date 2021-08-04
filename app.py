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
app.permanent_session_lifetime = timedelta(minutes=20)


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
    # api를 가져오려는 시점의 이전 발표시각에 업데이트된 데이터를 base_time, base_date로 설정 -> 취소
    # 기본값: api를 가져오는 날짜의 전날 23시에 발표된 데이터를 base_time, base_date로 설정
    base_date = yesterday_date
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

    try:
        items = res.json().get('response').get('body').get('items')
        print(items)
        weather_data = dict()
        for item in items['item']:
            # 기온
            if item['category'] == 'TMP':
                weather_data['tmp'] = item['fcstValue']

            # 기상상태
            if item['category'] == 'PTY':
                weather_code = item['fcstValue']

                if weather_code == '1':
                    weather_state = '비'
                elif weather_code == '2':
                    weather_state = '비/눈'
                elif weather_code == '3':
                    weather_state = '눈'
                elif weather_code == '4':
                    weather_state = '소나기'
                else:
                    weather_state = '없음'
            
                weather_data['code'] = weather_code
                weather_data['state'] = weather_state
    except:
        print('서버 점검 시간입니다.')
    
    

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
        userID = request.form['user_id']
        password = request.form['password']
        user = db.users.find_one({'userID' : userID, 'pw': password}, {'pw' : False})
        if user is None:
            return redirect(url_for('login'))
        session['userID'] = user['userID']
        return jsonify({"result" : "success"})
    if session_check():
        return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return jsonify({"result" : "success"})

def session_check():
    userID = session.get('userID')
    if userID is None:
        return False
    return True

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)