from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
import secrets
import dataclasses
import logging

logger = logging.getLogger(__name__)


class InvalidSessionError(Exception):
    pass


@dataclasses.dataclass
class TokenRecord:
    ses: webtalk_pb2.SessionToken
    user: webtalk_pb2.User


class SessionManager:
    def __init__(self):
        self._sessions = {}

    def get_user_for_session(self, ses):
        st = self._sessions.get(ses.token, None)
        if not st:
            raise InvalidSessionError()
        return st.user

    def _make_new_token(self):
        def generate():
            return webtalk_pb2.SessionToken(token=secrets.token_hex(16).encode("utf-8"))

        s = generate()
        while s.token in self._sessions:
            s = generate()
        return s

    def add_session(self, user):
        s = self._make_new_token()
        self._sessions[s.token] = TokenRecord(
            ses=s,
            user=user,
        )
        return s

    def remove_session(self, ses):
        u = self.get_user_for_session(ses)
        del self._sessions[ses.token]
        return u
