# -*- coding: utf-8 -*-
from flask import jsonify
from flask_restplus import Namespace, Resource, fields, reqparse
from collections import OrderedDict

Dialogue = Namespace('dialog', description='대화를 통한 진료과 도출')

model_dialogue = Dialogue.model('Dialog Model', {
    'message': fields.String(description='코코가 할 말'),
    'part_code': fields.String(description='인식한 부위의 코드'),
    'part_name': fields.String(description='인식한 부위의 이름'),
    'symptom_code': fields.List(fields.String(description='인식한 증상의 코드'))
})

@dialogue.route("")
class GetDialogue(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        