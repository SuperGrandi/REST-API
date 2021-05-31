import os
from flask import Flask, Blueprint
from flask_restplus import Api

from API.dialogue import Dialogue
from API.hospital import Hospital
from API.sendMessage import SendMessage

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

# set timezone Seoul
os.environ['TZ'] = 'Asia/Seoul'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './coco-huic-eb709454549b.json'

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, version='2.0', title='COCO API')
app.register_blueprint(blueprint)

api.add_namespace(Hospital, '/hospital')
api.add_namespace(SendMessage, '/sendMessage')
api.add_namespace(Dialogue, '/dialogue')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
