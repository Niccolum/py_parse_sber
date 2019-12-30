import json

from flask import Flask, Response, request
from marshmallow import Schema, fields


class AccountSchema(Schema):
    name = fields.Str()
    value = fields.Float()
    ccy = fields.Str()


class PaymentSchema(Schema):
    id = fields.Str()
    account = fields.Str()
    when = fields.DateTime(format='%Y.%m.%d')
    amount = fields.Float()
    currency = fields.Str()
    what = fields.Str()


app = Flask(__name__)

@app.route('/healthcheck')
def status():
    return Response(status=200)


@app.route('/send_account', methods=['POST'])
def send_account():
    data = request.json
    errors = AccountSchema(many=True).validate(data)
    if errors:
        return Response(response=json.dumps(errors), status=400)
    return Response(response=json.dumps(data), status=200)


@app.route('/send_payment', methods=['POST'])
def send_payment():
    data = request.json
    errors = PaymentSchema(many=True).validate(data)
    if errors:
        return Response(response=json.dumps(errors), status=400)
    return Response(response=json.dumps(data), status=200)


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)