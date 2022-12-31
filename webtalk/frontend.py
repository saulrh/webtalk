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
ID_MESSAGE_ENTRY_INPUT = "message-entry-input"
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


class MessageEntry(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Input(id=ID_MESSAGE_ENTRY_INPUT)

    class Changed(textual.message.Message):
        def __init__(self, sender: textual.message.MessageTarget, text: str) -> None:
            self.text = text
            super().__init__(sender)

    class Sent(textual.message.Message):
        def __init__(self, sender: textual.message.MessageTarget, text: str) -> None:
            self.text = text
            super().__init__(sender)

    async def on_input_submitted(self, message):
        await self.emit(MessageEntry.Sent(self, message.value))

    async def on_input_changed(self, message):
        await self.emit(MessageEntry.Changed(self, message.value))


class MessageList(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Placeholder()


class WebtalkApp(textual.app.App):

    CSS_PATH = "webtalk-frontend.css"
    # BINDINGS = [('q', 'quit', 'Log out and quit the app')]
    BINDINGS = []

    def __init__(self, *args, nick, **kwargs):
        self._nick = nick
        self._current_msg_id = None
        super().__init__(*args, **kwargs)

    # async def on_unmount(self) -> None:
    #     await self._logout()

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

    async def on_message_entry_sent(self, message) -> None:
        # Send it off to the server for finalization
        await self._stub.UpdateMessage(
            webtalk_pb2.UpdateMessageRequest(
                session=self._session,
                msg=webtalk_pb2.Message(
                    msg_id=self._current_msg_id,
                    text=message.text,
                    finalized=True,
                ),
            )
        )
        # Start a new message
        self._current_msg_id = None
        # And clear the input box
        inp = self.query_one("#" + ID_MESSAGE_ENTRY_INPUT, textual.widgets.Input)
        inp.value = ""

    async def on_message_entry_changed(self, message) -> None:
        response = await self._stub.UpdateMessage(
            webtalk_pb2.UpdateMessageRequest(
                session=self._session,
                msg=webtalk_pb2.Message(
                    text=message.text,
                    msg_id=self._current_msg_id,
                    finalized=False,
                ),
            )
        )
        self._current_msg_id = response.msg.msg_id

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
