# -*- coding: utf-8 -*-
import json
import time
import requests
import xmltodict
from flask_restplus import Namespace, Resource, abort, fields, reqparse
from database import Database

Hospital = Namespace('hospital', description='병원 찾기')

timetable = Hospital.model('timetable Model', {
    "day": fields.String("날짜별 오픈/마감 시간")
})

model_item = Hospital.model('hospital Model', {
    'name': fields.String(description='이름'),
    'div_name': fields.String(description='병/의원 구분'),
    'address': fields.String(description='주소'),
    'timetable': fields.Nested(timetable, description='시간표'),
    "tel_num": fields.String(description='전화번호'),
    "er_yn": fields.String(description='응급실 여부'),
    "latitude": fields.String(description='위도'),
    "longitude": fields.String(description='경도')
})

model_response_hospital = Hospital.model('response Hospital Model', {
    "result_code": fields.String(description='응답 코드'),
    'items': fields.Nested(model_item, desciption='병원 목록'),
    'time': fields.String(description='응답시간')
})


def get_hospital_info(hospital_id):
    res = requests.get(
        url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlBassInfoInqire",
        params={
            'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
            'HPID': hospital_id,
        }
    )
    return xmltodict.parse(res.text)


def insert_hospital_info():
    db = Database()

    sql = "select * from Hospital"
    sql_result = db.executeAll(sql)
    print(len(sql_result))
    for item in sql_result:
        while True:
            try:
                hos_info = get_hospital_info(item['hpid'])
                if "response" in hos_info:
                    break
            except:
                pass


        dgidIdName = hos_info["response"]["body"]['items']['item']['dgidIdName'] if 'dgidIdName' in hos_info["response"]["body"]['items']['item'] else None
        print(item["id"], dgidIdName)
        sql = "UPDATE Hospital set dgidIdName = %s where id = %s;"
        db.execute(sql, (dgidIdName, item["id"]))
        db.commit()

def get_hospital():
    db = Database()

    sql_result = db.executeAll(
        'SELECT COLUMN_NAME as col FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = \'Hospital\' AND TABLE_SCHEMA = \'coco_db\' LIMIT 1, 35;')
    col = ', '.join([res['col'] for res in sql_result])

    print(col)

    for page in range(1, 10000):
        res = requests.get(
            url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncListInfoInqire",
            params={
                'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
                'Q0': "서울특별시",
                'pageNo': str(page),
                'numOfRows': 100,
            }
        )
        res_json = xmltodict.parse(res.text)

        print(res_json)
        # print(res_json["response"]["body"]["items"])
        for item in res_json["response"]["body"]["items"]['item']:

            data = {
                'rnum': None,
                'dutyAddr':None,
                'dutyDiv': None,
                'dutyDivNam': None,
                'dgidIdName': None,
                'dutyEmcls': None,
                'dutyEmclsName': None,
                'dutyEryn': None,
                'dutyEtc': None,
                'dutyInf': None,
                'dutyMapimg': None,
                'dutyName': None,
                'dutyTel1': None,
                'dutyTel3': None,
                'dutyTime1c': None,
                'dutyTime1s': None,
                'dutyTime2c': None,
                'dutyTime2s': None,
                'dutyTime3c': None,
                'dutyTime3s': None,
                'dutyTime4c': None,
                'dutyTime4s': None,
                'dutyTime5c': None,
                'dutyTime5s': None,
                'dutyTime6c': None,
                'dutyTime6s': None,
                'dutyTime7c': None,
                'dutyTime7s': None,
                'dutyTime8c': None,
                'dutyTime8s': None,
                'hpid': None,
                'postCdn1': None,
                'postCdn2': None,
                'wgs84Lon': None,
                'wgs84Lat': None,
            }

            for k, v in dict(item).items():
                data[k] = v

            print(data)

            sql = "INSERT INTO Hospital " \
                  f"({col}) " \
                  "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            data_lists = list(data.values())
            db.execute(sql, data_lists)
            db.commit()
            # print(sql)

def get_hospital_by_location(lat, lon, dept_code, limit):
    db = Database()
    result = {'items': []}

    dept_code_dict = {
        "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과",
        "D007": "흉부외과",
        "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과",
        "D014": "비뇨기과",
        "D016": "재활의학과",
        "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
        "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
    }
    if dept_code == "EMR":
        dutyEryn = 1
    else:
        dutyEryn = 2

    sql = "SELECT *, " \
          f"(6371*acos(cos(radians({lat}))*cos(radians(wgs84Lat))*cos(radians(wgs84Lon) " \
          f"-radians({lon}))+sin(radians({lat}))*sin(radians(wgs84Lat)))) AS distance " \
          "FROM Hospital " \
          f"where dutyEryn = {dutyEryn} ORDER BY distance " \
          f"LIMIT 1, 1000" \

    sql_result = db.executeAll(sql)
    for item in sql_result:
        if item['distance'] is None or item['dgidIdName'] is None:
            continue

        hos_info = item['dgidIdName'].split(',')
        if dept_code == "EMR" or dept_code_dict[dept_code] in hos_info:
            data = {'name': item['dutyName'], 'div_name': item['dutyDivNam'], 'duty_div': item['dutyDiv'],
                    'dgidIdName': item['dgidIdName'],
                    'address': item['dutyAddr'], 'distance': int(float(item['distance']) * 1000), 'timetable': {
                    "monday": {
                        'start_time': item['dutyTime1s'],
                        'end_time': item['dutyTime1c']
                    },
                    "tuesday": {
                        'start_time': item['dutyTime2s'],
                        'end_time': item['dutyTime2c']
                    },
                    "wednesday": {
                        'start_time': item['dutyTime3s'],
                        'end_time': item['dutyTime3c']
                    },
                    "thursday": {
                        'start_time': item['dutyTime4s'],
                        'end_time': item['dutyTime4c'],
                    },
                    "friday": {
                        'start_time': item['dutyTime5s'],
                        'end_time': item['dutyTime5c'],
                    },
                    "saturday": {
                        'start_time': item['dutyTime6s'],
                        'end_time': item['dutyTime6c'],
                    },
                    "sunday": {
                        'start_time': item['dutyTime7s'],
                        'end_time': item['dutyTime7c']
                    },
                    "holiday": {
                        'start_time': item['dutyTime8s'],
                        'end_time': item['dutyTime8c']
                    }
                }, 'tel_num': item['dutyTel1'], 'er_yn': "Y" if item['dutyEryn'] == '1' else "N",
                    'latitude': item['wgs84Lat'], 'longitude': item['wgs84Lon']}

            result['items'].append(data)

        if len(result['items']) == limit:
            return result


def get_hospital_by_location_v1(lat, lon, dept_code, hos_count):
    count = 0
    start = time.time()
    escape = False

    for page in range(1, 10):
        if escape:
            break

        res = requests.get(
            url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncLcinfoInqire",
            params={
                'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
                "WGS84_LAT": lat,  # 위도
                "WGS84_LON": lon,  # 경도
                "pageNo": str(page),
                "numOfRows": 100,
            }
        )
        print("응답시간:", res.elapsed.total_seconds())
        dept_code_dict = {
            "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과",
            "D007": "흉부외과",
            "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과",
            "D014": "비뇨기과",
            "D016": "재활의학과",
            "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
            "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
        }
        dept_name = ""
        if dept_code != "EMR":
            dept_name = dept_code_dict[dept_code]

        print("Parse Data")
        result_dict = xmltodict.parse(res.text)
        # print(json.dumps(result_dict, ensure_ascii=False, indent=4))

        result_code = result_dict["response"]["header"]['resultCode']

        if not result_dict["response"]["body"]["items"]:
            abort(404)

        result = {'result_code': result_code}

        items = result_dict["response"]["body"]["items"]["item"]
        result['items'] = []

        for item in items:
            data = {}
            if item['dutyDiv'] in ['G', 'R']:
                continue

            # if int(range) < int(float(item['distance']) * 1000):
            # break

            hos_info = get_hospital_info(item['hpid'])
            # print(hos_info)
            hos_info_item = hos_info["response"]["body"]['items']['item']
            hos_info = hos_info["response"]["body"]['items']['item']['dgidIdName'].split(',')

            if dept_code == "EMR" or (dept_name in hos_info):
                count += 1
                data['name'] = item['dutyName']
                data['div_name'] = item['dutyDivName']
                data['duty_div'] = item['dutyDiv']
                data['address'] = item['dutyAddr']
                data['distance'] = int(float(item['distance']) * 1000)
                data['timetable'] = {
                    "monday": {
                        'start_time': hos_info_item['dutyTime1s'] if 'dutyTime1s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime1c'] if 'dutyTime1c' in hos_info_item else None,
                    },
                    "tuesday": {
                        'start_time': hos_info_item['dutyTime2s'] if 'dutyTime2s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime2c'] if 'dutyTime2c' in hos_info_item else None,
                    },
                    "wednesday": {
                        'start_time': hos_info_item['dutyTime3s'] if 'dutyTime3s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime3c'] if 'dutyTime3c' in hos_info_item else None
                    },
                    "thursday": {
                        'start_time': hos_info_item['dutyTime4s'] if 'dutyTime4s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime4c'] if 'dutyTime4c' in hos_info_item else None,
                    },
                    "friday": {
                        'start_time': hos_info_item['dutyTime5s'] if 'dutyTime5s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime5c'] if 'dutyTime5c' in hos_info_item else None,
                    },
                    "saturday": {
                        'start_time': hos_info_item['dutyTime6s'] if 'dutyTime6s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime6c'] if 'dutyTime6c' in hos_info_item else None,
                    },
                    "sunday": {
                        'start_time': hos_info_item['dutyTime7s'] if 'dutyTime7s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime7c'] if 'dutyTime7c' in hos_info_item else None
                    },
                    "holiday": {
                        'start_time': hos_info_item['dutyTime8s'] if 'dutyTime8s' in hos_info_item else None,
                        'end_time': hos_info_item['dutyTime8c'] if 'dutyTime8c' in hos_info_item else None
                    }
                }

                data['tel_num'] = item['dutyTel1']
                data['er_yn'] = "Y" if hos_info_item['dutyEryn'] == '1' else "N"
                data['latitude'] = item['latitude']
                data['longitude'] = item['longitude']

                if dept_code == "EMR" and data['er_yn'].lower() == "y":
                    result['items'].append(data)
                    escape = True
                    break

            if hos_count == count:
                escape = True
                break

    result['time'] = time.time() - start

    return result


@Hospital.route("")
class GetHospital(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        parser = reqparse.RequestParser()
        parser.add_argument('lat', type=str, required=True)
        parser.add_argument('lon', type=str, required=True)
        parser.add_argument('dept_code', type=str, required=True)
        parser.add_argument('range', type=str, required=True)
        parser.add_argument('emergency', type=str, required=True)

        args = parser.parse_args()

        self.lat = args['lat']
        self.lon = args['lon']
        self.dept_code = args['dept_code']
        self.range = args['range']
        self.emergency = args['emergency']

    @Hospital.response(200, 'OK', model=model_response_hospital)
    @Hospital.response(400, 'Bad Request')
    @Hospital.response(401, 'Unauthorized')
    @Hospital.doc(params={'lat': {'description': '위도', 'default': 37.550895, 'required': True}})
    @Hospital.doc(params={'lon': {'description': '경도', 'default': 127.0750224, 'required': True}})
    @Hospital.doc(params={
        'dept_code': {
            'description': '진료과 코드(D001:내과, D002:소아청소년과, D003:신경과, D004:정신건강의학과, \n'
                           'D005:피부과, D006:외과, D007:흉부외과,D008:정형외과, D009:신경외과, D010:성형외과,\n '
                           'D011:산부인과, D012:안과, D013:이비인후과, D014:비뇨기과, D016:재활의학과, \n'
                           'D017:마취통증의학과, D018:영상의학과, D019:치료방사선과, D020:임상병리과, \n'
                           'D021:해부병리과, D022:가정의학과,D023:핵의학과, D024:응급의학과, D026:치과, D034:구강악안면외과)',
            'enum': ['D001', 'D002', 'D003', 'D004', 'D005', 'D006', 'D007', 'D008', 'D009', 'D010', 'D011', 'D012',
                     'D013', 'D014', 'D016', 'D017', 'D018', 'D019', 'D020', 'D021', 'D022', 'D023', 'D024', 'D026',
                     'D034'],
            'required': True,
            'default': 'D001'
        }})
    @Hospital.doc(params={'range': {'description': '범위(미터 단위)', 'required': True, 'default': 300}})
    @Hospital.doc(
        params={'emergency': {'description': '응급실 여부(Y/N)', 'enum': ['Y', 'N'], 'required': True, 'default': 'N'}})
    def get(self):
        result = get_hospital_by_location(self.lat, self.lon, self.dept_code, self.emergency, 10)
        return result, 200
