from webtalk.protos import webtalk_pb2
import secrets
import logging
from webtalk import proto_utils

logger = logging.getLogger(__name__)


class NoPermissionToEditError(Exception):
    pass


class MessageFinalizedError(Exception):
    pass


class MessageManager:
    def __init__(self):
        self._messages = {}

    def _make_new_msg_id(self) -> int:
        def generate():
            return secrets.randbits(63)

        u = generate()
        while u in self._messages:
            u = generate()
        return u

    def update_message(
        self, new_message: webtalk_pb2.Message, author: webtalk_pb2.User
    ):
        if new_message.msg_id not in self._messages:
            return self.add_message(new_message, author)

        existing_message = self._messages[new_message.msg_id]
        logger.debug(existing_message)
        if existing_message.author.uid != author.uid:
            raise NoPermissionToEditError()
        if existing_message.finalized:
            raise MessageFinalizedError()
        # Finally, do updates for fields that are allowed to be updated
        existing_message.text = new_message.text
        if not existing_message.finalized and new_message.finalized:
            existing_message.finalized_time.GetCurrentTime()
            existing_message.finalized = True
        return existing_message

    def add_message(self, new_message: webtalk_pb2.Message, author: webtalk_pb2.User):
        new_message.msg_id = self._make_new_msg_id()
        new_message.created_time.GetCurrentTime()
        new_message.author.CopyFrom(author)
        self._messages[new_message.msg_id] = new_message
        return new_message

    def get_message(self, msg_id: int) -> webtalk_pb2.Message:
        return self._messages[msg_id]
