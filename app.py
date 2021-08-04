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

    # 사용자 정보
    userID = session['userID']
    userData = db.users.find_one({'userID': userID})
    area = userData['area']
    goingToOffice = userData['goingToOffice'] + '00'
    goingToOfficeEnd = str(int(goingToOffice) + 100)
    goingHome = userData['goingHome'] + '00'
    goingHomeEnd = str(int(goingHome) + 100)
    print(goingToOffice)

    # 동네 위경도
    village_data = db.grid.find_one({'village': area})
    x = village_data['x']
    y = village_data['y']
    
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

    payload = "serviceKey=" + service_key + "&" +\
        "pageNo=" + '1' + '&' +\
        "numOfRows=" + '530' + '&' +\
        "dataType=json" + "&" +\
        "base_date=" + base_date + "&" +\
        "base_time=" + base_time + "&" +\
        "nx=" + x + "&" +\
        "ny=" + y

    # print(payload)
    
    res = requests.get(weather_url + payload)
    
    clothes_txt = ''
    msg = ''
    img = ''
    max_TMP = ''
    min_TMP = ''
    umbrella = ''
    clothes_txt_t = ''
    msg_t = ''
    img_t = ''
    max_TMP_t = ''
    min_TMP_t = ''
    umbrella_t = ''

    try:
        items = res.json().get('response').get('body').get('items')
        # print(items)
        weather_data = dict()
        tmp_list = []
        state_list = []

        tmp_list_t = []
        state_list_t = []

        for item in items['item']:
            if item['fcstDate'] == today_date and item['fcstTime'] in [goingToOffice, goingToOfficeEnd, goingHome, goingHomeEnd]: 
                # 기온
                if item['category'] == 'TMP':
                    print(goingToOffice, goingToOfficeEnd)
                    tmp_list.append(int(item['fcstValue']))

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
                    state_list.append(weather_state)



            elif item['fcstDate'] == tomorrow_date and item['fcstTime'] in [goingToOffice, goingToOfficeEnd, goingHome, goingHomeEnd]:
                if item['category'] == 'TMP':
                    tmp_list_t.append(int(item['fcstValue']))
                elif item['category'] == 'PTY':
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
                    state_list_t.append(weather_state)

        print(tmp_list)
        print(state_list)

        max_TMP = max(tmp_list)
        min_TMP = min(tmp_list)
        umbrella = '날씨가 좋네요 :)'
        max_TMP_t = max(tmp_list_t)
        min_TMP_t = min(tmp_list_t)
        umbrella_t = '날씨가 좋네요 :)'

        for state in state_list:
            if state == '비':
                umbrella = '비가 와요. 우산을 꼭 챙겨주세요!'
            elif state == '비/눈':
                umbrella = '비 또는 눈이 와요. 우산 꼭 챙겨주세요!'
            elif state == '눈':
                umbrella = '눈이 와요. 우산을 꼭 챙기세요! 장갑도요!'
            elif state == '소나기':
                umbrella = '소나기가 와요. 우산을 꼭 챙겨주세요!'
        for state in state_list_t:
            if state == '비':
                umbrella_t = '비가 와요. 우산을 꼭 챙겨주세요!'
            elif state == '비/눈':
                umbrella_t = '비 또는 눈이 와요. 우산 꼭 챙겨주세요!'
            elif state == '눈':
                umbrella_t = '눈이 와요. 우산을 꼭 챙기세요! 장갑도요!'
            elif state == '소나기':
                umbrella_t = '소나기가 와요. 우산을 꼭 챙겨주세요!'

        
        for tmp in tmp_list:
            clothes_list = []
            msg_list = []
            img = ''
            if tmp <= 5:
                clothes_data = db.clothes.find_one({'high_TMP': 5})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                img = clothes_data['img']
            elif tmp <= 9:
                clothes_data = db.clothes.find_one({'high_TMP': 9})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            elif tmp <= 11:
                clothes_data = db.clothes.find_one({'high_TMP': 11})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            elif tmp <= 16:
                clothes_data = db.clothes.find_one({'high_TMP': 16})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            elif tmp <= 19:
                clothes_data = db.clothes.find_one({'high_TMP': 19})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            elif tmp <= 22:
                clothes_data = db.clothes.find_one({'high_TMP': 22})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            elif tmp <= 26:
                clothes_data = db.clothes.find_one({'high_TMP': 26})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']
            else:
                clothes_data = db.clothes.find_one({'high_TMP': 100})
                print(clothes_data)
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img:
                    img = clothes_data['img']

            clothes_txt = ', '.join(clothes_list)
            msg = '\n'.join(msg_list)


        for tmp in tmp_list_t:
            clothes_list = []
            msg_list = []
            img_t = ''
            if tmp <= 5:
                clothes_data = db.clothes.find_one({'high_TMP': 5})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                img_t = clothes_data['img']
            elif tmp <= 9:
                clothes_data = db.clothes.find_one({'high_TMP': 9})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            elif tmp <= 11:
                clothes_data = db.clothes.find_one({'high_TMP': 11})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            elif tmp <= 16:
                clothes_data = db.clothes.find_one({'high_TMP': 16})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            elif tmp <= 19:
                clothes_data = db.clothes.find_one({'high_TMP': 19})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            elif tmp <= 22:
                clothes_data = db.clothes.find_one({'high_TMP': 22})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            elif tmp <= 26:
                clothes_data = db.clothes.find_one({'high_TMP': 26})
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']
            else:
                clothes_data = db.clothes.find_one({'high_TMP': 100})
                print(clothes_data)
                clothes_list.append(clothes_data['clothes'])
                msg_list.append(clothes_data['msg'])
                if not img_t:
                    img_t = clothes_data['img']

            clothes_txt_t = ', '.join(clothes_list)
            msg_t = '\n'.join(msg_list)

        if max_TMP - min_TMP >= 10:
            msg = '일교차가 10°C 이상이에요. 감기 걸리지 않도록 두꺼운 옷 챙겨가세요!'
            
        if max_TMP_t - min_TMP_t >= 10:
            msg_t = '일교차가 10°C 이상이에요. 감기 걸리지 않도록 두꺼운 옷 챙겨가세요!'

    except Exception as ex:
        print('서버 점검 시간입니다. ', ex)
    
    

    return render_template('index.html', max_TMP=max_TMP, min_TMP=min_TMP, umbrella=umbrella, clothes_txt=clothes_txt, msg=msg, img=img, max_TMP_t=max_TMP_t, min_TMP_t=min_TMP_t, umbrella_t=umbrella_t, clothes_txt_t=clothes_txt_t, msg_t=msg_t, img_t=img_t )



@app.route('/update', methods=['POST'])
def update_user():
    pw = request.form['pw_give']
    pw2 = request.form['pw2_give']
    area = request.form['area_give']
    goingToOffice = request.form['goingToOffice_give'][0:2]
    goingHome = request.form['goingHome_give'][0:2]

    userID = session["userID"]

    db.users.update_one({'userID': userID}, {
                        '$set': {'pw': pw,
                                 'pw2': pw2,
                                 'area': area,
                                 'goingToOffice': goingToOffice,
                                 'goingHome': goingHome}})
    return jsonify({'result': 'success'})

@app.route('/update', methods=['GET'])
def get_update():
    if session_check() == False:
        return redirect(url_for('login'))
    all_sido = db.grid.distinct("sido")
    return render_template('update.html', all_sido=all_sido)

@app.route('/updatepw', methods=['GET'])
def get_updatepw():
    if session_check() == False:
        return redirect(url_for('login'))
    return render_template('updatepw.html', userID=session['userID'])

@app.route('/updatepw', methods=['POST'])
def update_userpw():
    pw = request.form['pw_give']
    pw2 = request.form['pw2_give']

    userID = session["userID"]

    db.users.update_one({'userID': userID}, {
                        '$set': {'pw': pw,
                                 'pw2': pw2}})
    return jsonify({'result': 'success'})

@app.route('/join', methods=['GET'])
def join_sido():
    if session_check():
        return redirect(url_for('main'))
    all_sido = db.grid.distinct("sido")
    return render_template('join.html', all_sido=all_sido)

@app.route('/join_sigungu', methods=['GET']) # 시도 dropdown 값 받음
def join_sigungu():
    sido_receive = request.args.get('sido_give') # 정해진 시도 값 받기
    all_sigungu = db.grid.distinct("sigungu",filter={'sido':sido_receive}) # 정해진 시도의 시군구 값 다 받기

    return jsonify({'result': 'success', 'all_sigungu': all_sigungu})

@app.route('/join_village', methods=['GET']) # 시군구 dropdown 값 받음
def join_village():
    sigungu_receive = request.args.get('sigungu_give') # 정해진 시군구 값 받기
    all_village = db.grid.distinct("village",filter={'sigungu':sigungu_receive}) # 정해진 시도의 시군구 값 다 받기

    return jsonify({'result': 'success', 'all_village': all_village})

@app.route('/join', methods=['POST'])
def post_join():
    msg = ''
    userID_receive = request.form['userID_give'] 
    pw_receive = request.form['pw_give'] 
    pw2_receive = request.form['pw2_give']
    area_receive = request.form['area_give'] # 동 만 받음
    goingToOffice_receive = request.form['goingToOffice_give']
    goingToOffice_receive2 = goingToOffice_receive[0:2]
    goingHome_receive = request.form['goingHome_give']
    goingHome_receive2 = goingHome_receive[0:2]

    userCheck = list(db.users.find({"userID":userID_receive}))
    


    join = {
        'userID': userID_receive, 
        'pw': pw_receive, 
        'pw2': pw2_receive,
        'area': area_receive, 
        'goingToOffice': goingToOffice_receive2, 
        'goingHome': goingHome_receive2
    }

    db.users.insert_one(join)

    session['userID'] = userID_receive
    
    if msg == '':
        msg = 'success'
    return jsonify({'result': msg})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        userID = request.form['user_id']
        password = request.form['password']
        user = db.users.find_one({'userID' : userID, 'pw': password}, {'pw' : False})
        if user is None:
            return jsonify({"result" : "fail"})
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