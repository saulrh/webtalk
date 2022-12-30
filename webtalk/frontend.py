from webtalk.protos import webtalk_pb2_grpc
from webtalk.protos import webtalk_pb2
import textual.app
import textual.widgets
import textual.containers
import textual.widgets

ID_MESSAGE_ENTRY = "message-entry"
ID_MESSAGE_ENTRY_INPUT = "message-entry-input"
ID_USER_LIST = "user-list"
ID_MESSAGE_LIST = "message-list"


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


class Username(textual.widgets.Static):
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

    def on_input_submitted(self, message):
        # Send it off to the server
        self.log("on_submit", message=message.value)
        # And then clear the box
        message.sender.value = ""


class MessageList(textual.widgets.Static):
    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Placeholder()


class WebtalkApp(textual.app.App):

    CSS_PATH = "webtalk-frontend.css"
    BINDINGS = []

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Header()
        yield textual.containers.Vertical(
            MessageList(id=ID_MESSAGE_LIST),
            MessageEntry(id=ID_MESSAGE_ENTRY),
        )
        yield textual.widgets.Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


def main():
    app = WebtalkApp()
    app.run()
