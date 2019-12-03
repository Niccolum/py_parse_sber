from flask import Flask, Response, request
import marshmallow

app = Flask(__name__)

@app.route('/status')
def status():
    return Response(status=200)


@app.route('/send_account', methods=['POST'])
def send_account():
    data = request.get_json()
    return Response(response=data, status=200)


@app.route('/send_payment', methods=['POST'])
def send_account():
    data = request.get_json()
    return Response(response=data, status=200)


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)