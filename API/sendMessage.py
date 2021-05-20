# -*- coding: utf-8 -*-
from flask import jsonify
from flask_restplus import Namespace, Resource, fields, reqparse
from collections import OrderedDict

SendMessage = Namespace('send message', description='Send message to DialogFlow')

model_send_message = SendMessage.model('send message params', {
    'session_id': fields.String(description='세션 ID', required=True),
    'message': fields.String(description='보낼 메시지', required=True)
})

model_response_send_message = SendMessage.model('response send message Model', {
    'message': fields.String(desciption='응답 메시지')
})


@SendMessage.response(200, 'OK', model=model_response_send_message)
@SendMessage.response(400, 'Bad Request')
@SendMessage.response(401, 'Unauthorized')
@SendMessage.route("")
class PostWebhook(Resource):

    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        parser = reqparse.RequestParser()
        parser.add_argument('session_id', type=str, required=True)
        parser.add_argument('message', type=str, required=True)
        args = parser.parse_args()
        self.__session_id = args['session_id']
        self.__message = args['message']
        self.__parameter = {}
        self.__fulfillment_text = ""

    def detect_intent_texts(self, project_id, session_id, text, language_code):
        from google.cloud import dialogflow
        location_id = "asia-northeast1"
        session_client = dialogflow.SessionsClient(
            client_options={"api_endpoint": f"{location_id}-dialogflow.googleapis.com"})
        session = (f"projects/{project_id}/locations/{location_id}/agent/sessions/{session_id}")
        print("Session path: {}\n".format(session))

        if text:
            text_input = dialogflow.TextInput(text=text, language_code=language_code)
            query_input = dialogflow.QueryInput(text=text_input)
            response = session_client.detect_intent(
                session=session, query_input=query_input)
            print(response)
            print(dict(response.query_result.parameters))
            self.__parameter = dict(response.query_result.parameters)
            print("Query text: {}".format(response.query_result.query_text))
            print(
                "Detected intent: {} (confidence: {})\n".format(
                    response.query_result.intent.display_name,
                    response.query_result.intent_detection_confidence,
                )
            )
            print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))
            self.__fulfillment_text = response.query_result.fulfillment_text

            return_json = OrderedDict()

            return_json["message"] = response.query_result.fulfillment_text
            return_json["parameter"] = dict(response.query_result.parameters)
            return_json["intent_display_name"] = response.query_result.intent.display_name
            return_json["intent_detection_confidence"] = response.query_result.intent_detection_confidence

            return return_json

    @SendMessage.expect(model_send_message)
    def post(self):
        project_id = 'coco-huic'
        return_json = self.detect_intent_texts(project_id, self.__session_id, self.__message, 'ko')


        return return_json
