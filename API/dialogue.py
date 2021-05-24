# -*- coding: utf-8 -*-
from flask import jsonify
from flask_restplus import Namespace, Resource, fields, reqparse
from collections import OrderedDict

Dialogue = Namespace('dialog', description='대화를 통한 진료과 도출')

response_model_dialogue = Dialogue.model('Dialog Model', {
    'message': fields.String(description='코코가 할 말'),
    'part_code': fields.String(description='인식한 부위의 코드'),
    'part_name': fields.String(description='인식한 부위의 이름'),
    'symptom_code': fields.List(fields.String(description='인식한 증상의 코드'))
})

model_dialogue = Dialogue.model("", {
    'message': fields.String(description='사용자 메시지'),
})

@Dialogue.route("")
class PostDialogue(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        parser = reqparse.RequestParser()
        parser.add_argument('message', type=str, required=True)

    @Dialogue.expect(model_dialogue)
    def post(self):
        ret_json = {
            "message": "코코가 할 말",
            "part_code": "인식한 부위의 코드",
            "part_name": "인식한 부위의 이름",
            "symtom_code": "인식한 증상의 코드"
        }
        return ret_json, 200
