import asyncio

from nio import AsyncClient


class MatrixClient:

    def __init__(self, homeserver: str, user: str, access_token: str, room_id: str):
        self.homeserver = homeserver
        self.user = user
        self.access_token = access_token
        self.room_id = room_id

    async def _send_message(self, message: str):
        client = AsyncClient(self.homeserver)
        client.access_token = self.access_token
        client.user_id = self.user

        await client.room_send(self.room_id,
                               message_type='m.room.message',
                               content={
                                   'msgtype': 'm.text',
                                   'body': message
                               })
        await client.close()

    def send_matrix_message(self, message: str):
        asyncio.get_event_loop().run_until_complete(
            self._send_message(message)
        )
