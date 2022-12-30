from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
from concurrent import futures
import grpc
from webtalk import session_manager
from webtalk import user_manager


RECENT_MESSAGES = []

class WebtalkServicer(webtalk_pb2_grpc.WebtalkServicer):
    def __init__(self, *args, **kwargs):
        self._sessions = session_manager.SessionManager()
        self._users = user_manager.UserManager()
        super().__init__(*args, **kwargs)

    def validate_session(self, ses, context):
        try:
            self._sessions.ensure_session_is_valid(request.session)
        except:
            context.abort(grpc.StatusCode.UNAUTHENTICATED)
        
    
    def Login(self, request, context):
        try:
            new_user = self._users.add_user(request.nick)
        except user_manager.NickTakenError:
            context.abort(grpc.StatusCode.ALREADY_EXISTS)

        return webtalk_pb2.LoginResponse(
            user=new_user,
            session=self._sessions.add_session(new_user)
        )

    def Logout(self, request, context):
        self._validate_session(request.session, context)
        u = self._sessions.get_user_for_session(request.session)
        self._sessions.remove_session(request.session)
        self._users.remove_user(u)
        return webtalk_pb2.LogoutResponse()

    def SendMessages(self, request_iterator, context):
        for request in request_iterator:
            self._validate_session(request.session, context)
            # TODO: handle send-message
        return webtalk_pb2.SendMessageResponse()

    def ReceiveMessages(self, request, context):
        self._validate_session(request.session, context)
        # TODO: handle send-message
        # yield webtalk_pb2.SendMessageResponse()



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    route_guide_pb2_grpc.add_RouteGuideServicer_to_server(WebtalkServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()