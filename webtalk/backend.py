from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
from concurrent import futures
import grpc
import grpc.aio
import asyncio
from webtalk import session_manager
from webtalk import user_manager
from webtalk import message_manager
from grpc_reflection.v1alpha import reflection
import logging

logger = logging.getLogger(__name__)


class WebtalkServicer(webtalk_pb2_grpc.WebtalkServicer):
    def __init__(self, *args, **kwargs):
        self._sessions = session_manager.SessionManager()
        self._users = user_manager.UserManager()
        self._messages = message_manager.MessageManager()
        self._update_queue = asyncio.Queue()
        super().__init__(*args, **kwargs)

    async def _validate_session(self, ses, context):
        try:
            return self._sessions.get_user_for_session(ses)
        except session_manager.InvalidSessionError:
            await context.abort(
                code=grpc.StatusCode.UNAUTHENTICATED, details="invalid session"
            )

    async def Login(self, request, context):
        logger.debug("incoming login: %s", request)

        try:
            new_user = self._users.add_user(request.nick)
            new_session = self._sessions.add_session(new_user)
            return webtalk_pb2.LoginResponse(
                user=new_user,
                session=new_session,
            )
        except user_manager.NickTakenError:
            await context.abort(
                grpc.StatusCode.ALREADY_EXISTS, details="nick is already taken"
            )

    async def Logout(self, request, context):
        logger.debug("incoming logout: %s", request)
        u = await self._validate_session(request.session, context)
        self._sessions.remove_session(request.session)
        self._users.remove_user(u)
        return webtalk_pb2.LogoutResponse()

    async def UpdateMessage(self, request, context):
        logger.debug("incoming update: %s", request)
        u = await self._validate_session(request.session, context)
        try:
            self._messages.update_message(request.msg, u)
        except message_manager.NoPermissionToEditError:
            await context.abort(
                code=grpc.StatusCode.PERMISSION_DENIED,
                details="you don't have permission to update that message",
            )
        except message_manager.MessageFinalizedError:
            await context.abort(
                code=grpc.StatusCode.INVALID_ARGUMENT,
                details="message already finalized and cannot be updated",
            )
        await self._update_queue.put(request.msg.msg_id)
        return webtalk_pb2.UpdateMessageResponse()

    async def UpdateMessages(self, request_iterator, context):
        for request in request_iterator:
            self.UpdateMessage(request, context)
        return webtalk_pb2.UpdateMessageResponse()

    async def ReceiveMessages(self, request, context):
        logger.debug("incoming receive: %s", request)
        u = await self._validate_session(request.session, context)
        while True:
            updated_msg_id = await self._update_queue.get()
            updated_msg = self._message_manager.get_message(updated_msg_id)
            logger.debug("outgoing message: %s", updated_msg)
            yield ReceiveMessageResponse(
                {
                    "msg": updated_msg,
                }
            )
            self._update_queue.task_done()


async def serve_async():
    logging.basicConfig(encoding="utf-8", level=logging.DEBUG)

    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    webtalk_pb2_grpc.add_WebtalkServicer_to_server(WebtalkServicer(), server)
    reflection.enable_server_reflection(
        (
            webtalk_pb2.DESCRIPTOR.services_by_name["Webtalk"].full_name,
            reflection.SERVICE_NAME,
        ),
        server,
    )
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()


def serve():
    asyncio.run(serve_async())
