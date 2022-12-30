from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
import secrets
import dataclasses


class InvalidSessionError(Exception):
    pass


@dataclasses.dataclass
class TokenRecord:
    ses = webtalk_pb2.SessionToken
    user = webtalk_pb2.User


class SessionManager:
    def __init__(self):
        self._sessions = {}


    def is_session_valid(self, ses):
        return ses.token in self._sessions

    def ensure_session_is_valid(self, ses):
        if not self.is_session_valid(ses):
            raise InvalidSessionError()

    def _make_new_token(self):
        def generate():
            return webtalk_pb2.SessionToken(token=secrets.token_bytes(8))

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


    def remove_session(self, ses):
        self.ensure_session_is_valid(ses)
        u = self._sessions[ses.token].user
        del self._sessions[ses.token]
        return u
        

    def get_user_for_session(self, ses):
        self.ensure_session_is_valid(ses)
        return self._sessions[ses.token].user
