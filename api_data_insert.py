from openpyxl import load_workbook
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.dbweather

# data_only=True로 해줘야 수식이 아닌 값으로 받아온다.
load_wb = load_workbook('기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(20210401).xlsx', data_only=True)

# 시트 이름으로 불러오기
load_ws = load_wb['최종 업데이트 파일_20210401']

code = load_ws.cell(3775, 2).value  # 행정구역코드
print(code)

for i in range(2, 3776):
    code = load_ws.cell(i, 2).value
    sido = load_ws.cell(i, 3).value
    sigungu = load_ws.cell(i, 4).value
    village = load_ws.cell(i, 5).value
    x = load_ws.cell(i, 6).value
    y = load_ws.cell(i, 7).value

    data = ({'code': code, 'sido': sido, 'sigungu': sigungu, 'village': village, 'x': x, 'y': y})
    print(data)
    db.grid.insert_one(data)