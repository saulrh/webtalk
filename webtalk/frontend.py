from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
import textual.app
import click
import datetime
import textual.widgets
import textual.message
import textual.containers
import textual.widgets
import grpc.aio
import asyncio
from google.protobuf import timestamp_pb2
from webtalk import proto_utils

ID_MESSAGE_ENTRY = "message-entry"
ID_USER_LIST = "user-list"
ID_MESSAGE_LIST = "message-list"

HEARTBEAT_FREQUENCY = datetime.timedelta(seconds=30)

#      +-----------------------------------------------+
#      |              header                           |
#      +-----------------------------------------------+
#                                             +--------+
#         username | message                  |username|
#                                             |username|
#         username | message                  |username|
#                                             |        |
#         username | message                  |        |
#                                             +--------+
#      +-----------------------------------------------+
#      |              text entry                       |
#      +-----------------------------------------------+
#      +-----------------------------------------------+
#      |              footer                           |
#      +-----------------------------------------------+
#


class MessageText(textual.widgets.Static):
    pass


class Username(textual.widgets.Label):
    pass


class UserList(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        # will fill with Username
        yield textual.containers.Vertical()


class Message(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield Username()
        yield MessageText()


class MessageEntry(textual.widgets.Input):
    pass


class MessageList(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Placeholder()


class WebtalkApp(textual.app.App):

    CSS_PATH = "webtalk-frontend.css"
    # BINDINGS = [('q', 'quit', 'Log out and quit the app')]
    BINDINGS = []

    def __init__(self, *args, nick, **kwargs):
        self._nick = nick
        super().__init__(*args, **kwargs)

    async def on_unmount(self) -> None:
        await self._logout()

    async def on_mount(self) -> None:
        await self._login()

    async def _login(self) -> None:
        self._channel = grpc.aio.insecure_channel("localhost:50051")
        self._stub = webtalk_pb2_grpc.WebtalkStub(self._channel)
        login_response = await self._stub.Login(
            webtalk_pb2.LoginRequest(nick=self._nick)
        )
        self._session = login_response.session
        self._user = login_response.user
        self._receive_task = asyncio.create_task(self._do_receive_messages())
        self._heartbeat_task = asyncio.create_task(self._do_heartbeat())

    async def _logout(self) -> None:
        await self._stub.Logout(webtalk_pb2.LogoutRequest(session=self._session))
        await self._channel.close()

    async def _do_heartbeat(self) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_FREQUENCY.total_seconds())
            await self._stub.Heartbeat(webtalk_pb2.HeartbeatRequest())

    async def on_input_submitted(self, message) -> None:
        # Finalize it and send it off to the server
        self.log("on_submit", message=message.value)
        now = proto_utils.timestamp_now()
        request = webtalk_pb2.UpdateMessageRequest()
        request.session.CopyFrom(self._session)
        request.msg.text = message.value
        request.msg.finalized = True
        await self._stub.UpdateMessage(request)
        # And then clear the box
        message.sender.value = ""

    async def _do_receive_messages(self) -> None:
        self.log("RECEIVE MESSAGES")
        for response in await self._stub.ReceiveMessages(
            webtalk_pb2.ReceiveMessagesRequest(session=self._session)
        ):
            self.log(response)

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Header()
        yield textual.containers.Vertical(
            MessageList(id=ID_MESSAGE_LIST),
            MessageEntry(id=ID_MESSAGE_ENTRY),
        )
        yield textual.widgets.Footer()


@click.command()
@click.option("--nick", required=True, type=str)
def present_frontend(nick):
    app = WebtalkApp(nick=nick)
    app.run()


if __name__ == "__main__":
    present_frontend()
