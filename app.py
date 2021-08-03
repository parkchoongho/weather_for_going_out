from flask import Flask, render_template
from pymongo import MongoClient
# from bson.objectid import ObjectId
import datetime  # 날짜시간모듈
from datetime import date, datetime, timedelta  # 현재 날짜 외의 날짜 구하기 위한 모듈
import requests
import json  # json 파일 파싱하여 데이터 읽는 모듈

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbweather

# @app.route('/', methods=['GET'])
# def home():
#     return render_template('index.html')

@app.route('/')
def main():
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
    if now.hour < 2 or (now.hour==2 and now.minute<=10): # 0시~2시 10분 사이
        base_date=yesterday_date # 구하고자 하는 날짜가 어제의 날짜
        base_time="2300"
    elif now.hour<5 or (now.hour==5 and now.minute<=10): # 2시 11분~5시 10분 사이
        base_date=today_date
        base_time="0200"
    elif now.hour<8 or (now.hour==8 and now.minute<=10): # 5시 11분~8시 10분 사이
        base_date=today_date
        base_time="0500"
    elif now.hour<=11 or now.minute<=10: # 8시 11분~11시 10분 사이
        base_date=today_date
        base_time="0800"
    elif now.hour<14 or (now.hour==14 and now.minute<=10): # 11시 11분~14시 10분 사이
        base_date=today_date
        base_time="1100"
    elif now.hour<17 or (now.hour==17 and now.minute<=10): # 14시 11분~17시 10분 사이
        base_date=today_date
        base_time="1400"
    elif now.hour<20 or (now.hour==20 and now.minute<=10): # 17시 11분~20시 10분 사이
        base_date=today_date
        base_time="1700" 
    elif now.hour<23 or (now.hour==23 and now.minute<=10): # 20시 11분~23시 10분 사이
        base_date=today_date
        base_time="2000"
    else: # 23시 11분~23시 59분
        base_date=today_date
        base_time="2300"

    # 날짜, 예보시각, 위경도 정보 받아오는 변수로 수정해야 함.
    payload = "serviceKey=" + service_key + "&" +\
        "pageNo=" + '1' + '&' +\
        "numOfRows=" + '270' + '&' +\
        "dataType=json" + "&" +\
        "base_date=" + today_date + "&" +\
        "base_time=" + "0630" + "&" +\
        "nx=" + "62" + "&" +\
        "ny=" + "120"

    print(payload)
    
    res = requests.get(weather_url + payload)
    items = res.json().get('response').get('body').get('items')

    print(items)

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


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)