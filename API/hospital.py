# -*- coding: utf-8 -*-
from datetime import datetime

import jwt
import requests
import xmltodict
from flask import request
from flask_restplus import Namespace, Resource, abort, fields, reqparse

Hospital = Namespace('hospital', description='병원 찾기')

announcement_model = Hospital.model('announcement_model', {
    'id': fields.String(description='공지사항 ID'),
    'title': fields.String(description='공지사항 제목'),
    'body': fields.String(description='공지사항 body'),
    'creator': fields.String(description="공지사항 작성자"),
    'created': fields.DateTime(description='최초 작성 일자'),
    'modified': fields.DateTime(description='수정 일자'),
})

announcement_response_model = Hospital.model('announcement response model', {
    'results': fields.List(fields.Nested(announcement_model), description="공지 목록"),
})


@Hospital.route("")
class GetHospital(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        parser = reqparse.RequestParser()
        parser.add_argument('lat', type=str)
        parser.add_argument('lon', type=str)
        parser.add_argument('dept_code', type=str)
        parser.add_argument('range', type=str)
        args = parser.parse_args()

        self.__lat = args['lat']
        self.__lon = args['lon']
        self.__dept_code = args['dept_code']
        self.__range = args['range']

    def get_hospital_info(self, hospital_id):
        res = requests.get(
            url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlBassInfoInqire",
            params={
                'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
                'HPID': hospital_id,
            }
        )
        return xmltodict.parse(res.text)

    @Hospital.response(200, 'OK', model=announcement_response_model)
    @Hospital.response(400, 'Bad Request')
    @Hospital.response(401, 'Unauthorized')
    @Hospital.doc(params={'lat': '위도'})
    @Hospital.doc(params={'lon': '경도'})
    @Hospital.doc(params={'dept_code': '진료과 코드\n(D001:내과, D002:소아청소년과, D003:신경과, D004:정신건강의학과, \n'
                                       'D005:피부과, D006:외과, D007:흉부외과,D008:정형외과, D009:신경외과, D010:성형외과,\n '
                                       'D011:산부인과, D012:안과, D013:이비인후과, D014:비뇨기과, D016:재활의학과, \n'
                                       'D017:마취통증의학과, D018:영상의학과, D019:치료방사선과, D020:임상병리과, \n'
                                       'D021:해부병리과, D022:가정의학과,D023:핵의학과, D024:응급의학과, D026:치과, D034:구강악안면외과)'
                          })
    @Hospital.doc(params={'range': '범위(미터 단위)'})
    def get(self):
        dept_code_dict = {
            "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과",
            "D007": "흉부외과",
            "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과",
            "D014": "비뇨기과",
            "D016": "재활의학과",
            "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
            "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
        }
        dept_name = dept_code_dict[self.__dept_code]

        result = {}
        print("Load Data")
        res = requests.get(
            url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncLcinfoInqire",
            params={
                'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
                "WGS84_LAT": self.__lat,  # 위도
                "WGS84_LON": self.__lon,  # 경도
                "numOfRows": 100,
            }
        )

        if res.status_code == 500:
            abort(404)

        print(res.elapsed.total_seconds())

        print("Parse Data")
        result_dict = xmltodict.parse(res.text)
        result_code = result_dict["response"]["header"]['resultCode']

        print()

        if not result_dict["response"]["body"]["items"]:
            abort(404)

        result['result_code'] = result_code
        items = result_dict["response"]["body"]["items"]["item"]
        result['items'] = []
        for item in items:
            data = {}

            if item['dutyDiv'] in ['G', 'R']:
                continue

            if int(self.__range) < int(float(item['distance']) * 1000):
                break

            hos_info = self.get_hospital_info(item['hpid'])
            hos_info = hos_info["response"]["body"]['items']['item']['dgidIdName'].split(',')

            if dept_name in hos_info:
                data['name'] = item['dutyName']
                data['address'] = item['dutyAddr']
                data['start_time'] = item['startTime']
                data['end_time'] = item['endTime']
                data['tel_num'] = item['dutyTel1']
                data['latitude'] = item['latitude']
                data['longitude'] = item['longitude']

                result['items'].append(data)

        print(result)
        return result, 200
