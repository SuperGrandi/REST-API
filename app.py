from flask import Flask

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)