from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
import secrets


class NickTakenError(Exception):
    pass


class UserManager:
    def __init__(self):
        self._users = {}

    def _make_new_uid(self):
        def generate():
            return secrets.randbits(63)

        u = generate()
        while u in self._users:
            u = generate()
        return u

    def add_user(self, nick):
        for _, user in self._users.items():
            if user.nick == nick:
                raise NickTakenError()

        new_uid = self._make_new_uid()
        new_user = webtalk_pb2.User(
            uid=new_uid,
            nick=nick,
        )
        self._users[new_user.uid] = new_user
        return new_user

    def remove_user(self, user):
        if user.uid not in self._users:
            raise KeyError()
        del self._users[user.uid]
