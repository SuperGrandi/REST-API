import os

from flask import Flask, Blueprint
from flask_restplus import Api

from API.hospital import Hospital

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

# set timezone Seoul
os.environ['TZ'] = 'Asia/Seoul'

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, version='2.0', title='병원찾기 API')
app.register_blueprint(blueprint)

api.add_namespace(Hospital, '/hospital')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)