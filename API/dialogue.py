# -*- coding: utf-8 -*-
from flask import jsonify
from flask_restplus import Namespace, Resource, fields, reqparse
from collections import OrderedDict

from API import hospital
from API.sendMessage import detect_intent_texts
from database import Database
import requests
import ast

Dialogue = Namespace('dialogue', description='대화를 통한 진료과 도출')

response_model_dialogue = Dialogue.model('Dialogue Model', {
    'session_id': fields.Integer(description='세션ID'),
    'message': fields.String(description='코코가 할 말'),
    'part_code': fields.String(description='인식한 부위의 코드'),
    'part_name': fields.String(description='인식한 부위의 이름'),
    'symptom_code': fields.List(fields.String(description='인식한 증상의 코드'))
})

model_dialogue = Dialogue.model("", {
    'session_id': fields.Integer(description='세션ID'),
    'message': fields.String(description='사용자 메시지'),
    "latitude": fields.String(description='위도', required=False),
    "longitude": fields.String(description='경도', required=False),
})

coco_db = Database()

dept_code_dict = {
    "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과",
    "D007": "흉부외과",
    "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과",
    "D014": "비뇨기과",
    "D016": "재활의학과",
    "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
    "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
}


@Dialogue.route("")
class PostDialogue(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        parser = reqparse.RequestParser()
        parser.add_argument('session_id', type=int, required=True)
        parser.add_argument('message', type=str, required=True)
        parser.add_argument('latitude', type=str, required=False)
        parser.add_argument('longitude', type=str, required=False)

        args = parser.parse_args()

        self.session_id = int(args['session_id'])
        self.message = args['message']
        self.__lat = args['latitude']
        self.__lon = args['longitude']

        if self.session_id == 0:
            self.session_id = generate_session_id()

        print(f'세션ID: {self.session_id}')
        self.part_data, self.symptom_data, self.disease_data, self.medical_department = load_data()

    def query_by_part_symptom(self, dialog_param, stored_data):
        hospital_info = None
        # 부위 특정
        if len(dialog_param['PART_NAME']) > 0:
            print(f'부위: {dialog_param["PART_NAME"]}')
            for part_item in self.part_data:
                if dialog_param['PART_NAME'] == part_item['part_name']:
                    print(part_item)
                    stored_data['part_code'] = part_item['part_code']
                    stored_data['part_name'] = part_item['part_name']

        # 증상 목록
        if len(dialog_param['SYMPTOM_NAME']) > 0:
            print(f'증상: {dialog_param["SYMPTOM_NAME"]}')
            for symptom_item in self.symptom_data:
                if dialog_param['SYMPTOM_NAME'] == symptom_item['symptom_name'] and symptom_item['symptom_code'] not in \
                        stored_data['symptom_code']:
                    stored_data['symptom_code'].append(symptom_item['symptom_code'])

        if stored_data['part_code'] is None:  # 부위 정보가 없는 경우 질의
            stored_data['message'] = '어디가 불편하신가요?'

        elif len(stored_data['symptom_code']) == 0:  # 증상 정보가 없는 경우 질의
            stored_data['message'] = f'{stored_data["part_name"]}이(가) 어떻게 아프신가요?'

        else:
            # 질병 후보군
            disease_result = get_disease(self.disease_data, stored_data)

            # 진료과 후보군
            departments = []
            department_weights = {}
            sum_department_weights = 0
            for disease_item in disease_result:
                if disease_item['medical_dept'] not in departments:
                    for dept in disease_item['medical_dept']:
                        departments.append(dept)
                        if dept not in department_weights:
                            department_weights[dept] = 0
                        department_weights[dept] += 1
                        sum_department_weights += 1
            departments = list(set(departments))  # 중복 제거

            # 가장 가능성 높은 진료과 추정
            most_department = max(department_weights, key=department_weights.get)
            department_per = department_weights[most_department] / sum_department_weights
            if department_per > 0.5:
                departments = [most_department]

            print(departments)
            print(department_weights)

            if len(departments) == 1:
                try:
                    info = hospital.get_hospital_by_location(self.__lat, self.__lon, departments[0], 1)
                    hospital_info = {'hospital_info': info["items"][0]}
                    hospital_name = hospital_info['hospital_info']['name']
                    stored_data[
                        'message'] = f'여기서 가장 가까운 {dept_code_dict[departments[0]]}인 {hospital_name}을(를) 안내해 드릴게요.'
                except:
                    stored_data['message'] = f'어디 계신지 모르겠어요.'

            elif len(disease_result) == 0:
                stored_data['message'] = '진료과를 찾지 못했습니다.'
            else:
                stored_data['message'] = '조금 더 자세히 말씀해 주세요.'

        return stored_data, hospital_info

    def emergency_query(self, dialog_param, stored_data):
        hospital_info = None

        info = hospital.get_hospital_by_location(self.__lat, self.__lon, "EMR", 1)
        print(info)
        hospital_info = {'hospital_info': info["items"][0]}
        hospital_name = hospital_info['hospital_info']['name']
        print(hospital_name)
        message = f'가장 가까운 응급실이 있는 곳은 {hospital_name} 이에요!'

        stored_data = {
            "session_id": self.session_id,
            "message": message,
            "part_code": None,
            "part_name": None,
            "symptom_code": "EMR"
        }
        return stored_data, hospital_info

    def emergency_call(self, dialog_param, stored_data):
        stored_data = {
            "session_id": self.session_id,
            "message": "119에 전화할게요!",
            "part_code": None,
            "part_name": None,
            "symptom_code": "EMR"
        }
        return stored_data

    @Dialogue.expect(model_dialogue)
    def post(self):

        sql = f'SELECT * FROM Dialogue WHERE session_id={int(self.session_id)} ORDER BY id DESC LIMIT 1'
        stored_data = coco_db.executeOne(sql)
        hospital_info = None
        
        # 대화 시작 시
        print(f'rowcount: {coco_db.getCursor().rowcount}')
        if coco_db.getCursor().rowcount == 0:
            ret_json = stored_data = {
                'session_id': self.session_id,
                'message': '',
                'part_code': None,
                'part_name': None,
                'symptom_code': []
            }
        else:
            stored_data['symptom_code'] = ast.literal_eval(stored_data['symptom_code'])
            ret_json = stored_data

        dialog_data = user_query(self.message)
        print(dialog_data)


        dialog_intent = dialog_data['intent_display_name']
        dialog_param = dialog_data['parameter']
        if 'PART_NAME' not in dialog_param:
            dialog_param['PART_NAME'] = ''
        if 'SYMPTOM_NAME' not in dialog_param:
            dialog_param['SYMPTOM_NAME'] = ''

        # 부위 질의 or 증상 질의
        if dialog_intent == '부위 질의' or dialog_intent == '증상 질의':
            stored_data, hospital_info = self.query_by_part_symptom(dialog_param, stored_data)
        # 응급실 질의
        elif dialog_intent == '응급실 질의':
            stored_data, hospital_info = self.emergency_query(dialog_param, stored_data)
        # 응급실 호출
        elif dialog_intent == '응급실 호출':
            stored_data = self.emergency_call(dialog_param, stored_data)
        # 기타 스몰토크
        else:
            stored_data = etc_intents(dialog_data, stored_data)

        ret_json = {
            "session_id": self.session_id,
            "message": stored_data['message'],
            "part_code": stored_data['part_code'],
            "part_name": stored_data['part_name'],
            "symptom_code": stored_data['symptom_code']
        }
        insert_dialogue(ret_json)

        if hospital_info:
            ret_json.update(hospital_info)

        return ret_json, 200

def load_data():
    # Part
    sql = 'SELECT * FROM Part'
    part_data = coco_db.executeAll(sql)

    # Symptom
    sql = 'SELECT * FROM Symptom'
    symptom_data = coco_db.executeAll(sql)

    # Disease
    sql = 'SELECT * FROM Disease'
    disease_data = coco_db.executeAll(sql)
    for disease_item in disease_data:
        disease_item['symptom_code'] = disease_item['symptom_code'].split(',')
        disease_item['medical_dept'] = disease_item['medical_dept_code'].split(',')
        disease_item['synonym'] = disease_item['synonym'].split(',')

    # Medical Department
    sql = 'SELECT * FROM MedicalDepartment'
    medical_department = coco_db.executeAll(sql)

    return part_data, symptom_data, disease_data, medical_department


def generate_session_id():
    sql = 'INSERT INTO SessionInfo VALUES ()'
    coco_db.execute(sql)
    coco_db.commit()
    return coco_db.getCursor().lastrowid


def insert_dialogue(data):
    sql = 'INSERT INTO Dialogue \
        (session_id, message, part_code, part_name, symptom_code) \
        VALUES (%s, %s, %s, %s, %s)'
    coco_db.execute(sql, (
    data['session_id'], data['message'], data['part_code'], data['part_name'], str(data['symptom_code'])))
    coco_db.commit()


def get_part(part_data, part_code):
    for part_item in part_data:
        if part_item['part_code'] == part_code:
            return part_item
    return None


def get_symptom(symptom_data, symptom_code):
    for symptom_item in symptom_data:
        if symptom_item['symptom_code'] == symptom_code:
            return symptom_item
    return None


def get_disease(disease_data, inputed_data):
    disease_result = []
    for disease_item in disease_data:
        symptom_matched = True

        if inputed_data['part_code'] != disease_item['part_code']:
            continue  # 부위가 다르면 다음 질병 조회

        for inputed_symptom in inputed_data['symptom_code']:
            if inputed_symptom not in disease_item['symptom_code']:
                symptom_matched = False
                break  # 다음 질병 조회

        if symptom_matched == True:
            disease_result.append(disease_item)
    return disease_result


def user_query(query):
    project_id = 'coco-huic'
    response = detect_intent_texts(project_id, "test", query, 'ko')
    return response


def user_department_search_old(part_data, symptom_data, disease_data, inputed_data=None):
    if inputed_data is None:
        inputed_data = {
            'message': '듣고 있어요.',
            'part_code': None,
            'part_name': None,
            'symptom_code': []
        }

    print('')
    print(inputed_data)
    print(inputed_data['message'])
    user_input = input('> 입력: ')

    dialog_data = user_query(user_input)
    print(dialog_data)
    dialog_param = dialog_data['parameter']

    # 부위 특정
    part_name = ''
    if 'PART_NAME' in dialog_param and len(dialog_param['PART_NAME']) > 0:
        print(f'부위: {dialog_param["PART_NAME"]}')
        for part_item in part_data:
            if dialog_param['PART_NAME'] == part_item['part_name']:
                inputed_data['part_code'] = part_item['part_code']
                inputed_data['part_name'] = part_item['part_name']

    # 증상 목록
    if len(dialog_param['SYMPTOM_NAME']) > 0:
        print(f'증상: {dialog_param["SYMPTOM_NAME"]}')
        for symptom_item in symptom_data:
            if dialog_param['SYMPTOM_NAME'] == symptom_item['symptom_name'] and symptom_item['symptom_code'] not in \
                    inputed_data['symptom_code']:
                inputed_data['symptom_code'].append(symptom_item['symptom_code'])

    if inputed_data['part_code'] is None:  # 부위 정보가 없는 경우 질의
        inputed_data['message'] = '어디가 불편하신가요?'
        return user_department_search_old(inputed_data)
    elif len(inputed_data['symptom_code']) == 0:  # 증상 정보가 없는 경우 질의
        inputed_data['message'] = f'{inputed_data["part_name"]}이(가) 어떻게 아프신가요?'
        return user_department_search_old(inputed_data)

    # 질병 후보군
    disease_result = get_disease(disease_data, inputed_data)

    # 진료과 후보군
    departments = []
    department_weights = {}
    sum_department_weights = 0
    for disease_item in disease_result:
        if disease_item['medical_dept'] not in departments:
            for dept in disease_item['medical_dept']:
                departments.append(dept)
                if dept not in department_weights:
                    department_weights[dept] = 0
                department_weights[dept] += 1
                sum_department_weights += 1
    departments = list(set(departments))  # 중복 제거

    # 가장 가능성 높은 진료과 추정
    most_department = max(department_weights, key=department_weights.get)
    department_per = department_weights[most_department] / sum_department_weights
    if department_per > 0.5:
        departments = [most_department]

    if len(departments) == 1:
        print(f'진료과 {departments[0]}를 안내해 드리겠습니다.')
        return departments[0]
    elif len(disease_result) == 0:
        print('진료과를 찾지 못했습니다.')
        return None
    print(f'후보 질병 수: {len(disease_result)}')
    print(f'후보 진료과 수: {len(departments)}')
    print(department_weights)
    return user_department_search_old(part_data, symptom_data, disease_data, inputed_data)