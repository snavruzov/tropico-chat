import json
from base64 import b64encode, b64decode
from dataclasses import dataclass


@dataclass
class RabbitBody:
    message: str
    session_id: str

    def encode(self):
        return b64encode(self.json().encode())

    @staticmethod
    def decode(encoded):
        data = json.loads(b64decode(encoded))
        return RabbitBody(**data)

    def json(self):
        return json.dumps({'message': self.message, 'session_id': self.session_id})
