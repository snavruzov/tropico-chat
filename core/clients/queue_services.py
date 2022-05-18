import aiormq

from core.clients.schemas import RabbitBody
from core.config import RABBIT_USERNAME, RABBIT_PASSWORD, RABBIT_HOST


class MessageQueueClient:

    def __init__(self, exchange_name):
        self.exchange_name = exchange_name

    async def push_to_rabbit(self, *, message: str, session_id: str):
        connection = await aiormq.connect("amqp://{}:{}@{}/".format(RABBIT_USERNAME, RABBIT_PASSWORD, RABBIT_HOST))
        channel = await connection.channel()

        request = RabbitBody(message, session_id)

        await channel.exchange_declare(
            exchange=self.exchange_name, exchange_type='direct'
        )

        await channel.basic_publish(
            request.encode(),
            routing_key='tropico_chat',
            exchange=self.exchange_name,
            properties=aiormq.spec.Basic.Properties(
                delivery_mode=2
            )
        )
