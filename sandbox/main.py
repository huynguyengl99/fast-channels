from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse

from sandbox.consumer import (
    AnalyticsConsumer,
    ChatConsumer,
    NotificationConsumer,
    ReliableChatConsumer,
)
from sandbox.layers import setup_layers

setup_layers()

app = FastAPI()

# ----------------- HTML Client -----------------
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Group Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'></ul>
        <script>
            // WebSocket connections for different layer types
            var wsChat = new WebSocket("ws://localhost:8080/ws/chat");
            var wsNotifications = new WebSocket("ws://localhost:8080/ws/notifications");
            var wsReliable = new WebSocket("ws://localhost:8080/ws/reliable");

            // Handle chat messages
            wsChat.onmessage = function(event) {
                addMessage("Chat: " + event.data, "chat");
            };

            // Handle notifications
            wsNotifications.onmessage = function(event) {
                addMessage("Notification: " + event.data, "notification");
            };

            // Handle reliable messages
            wsReliable.onmessage = function(event) {
                addMessage("Reliable: " + event.data, "reliable");
            };

            function addMessage(text, type) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                message.className = type;
                var content = document.createTextNode(text);
                message.appendChild(content);
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            }

            function sendMessage(event) {
                var input = document.getElementById("messageText");
                var message = input.value;

                // Send to all WebSocket connections
                if (wsChat.readyState === WebSocket.OPEN) {
                    wsChat.send(message);
                }
                if (wsReliable.readyState === WebSocket.OPEN) {
                    wsReliable.send(message);
                }

                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

home_router = APIRouter(tags=["home"])


@home_router.get("/")
async def home():
    return HTMLResponse(html)


app.include_router(home_router)

# ----------------- WebSocket Sub-App -----------------
ws_router = FastAPI()

# WebSocket routes using different channel layers
ws_router.add_websocket_route("/chat", ChatConsumer.as_asgi())
ws_router.add_websocket_route("/reliable", ReliableChatConsumer.as_asgi())
ws_router.add_websocket_route("/notifications", NotificationConsumer.as_asgi())
ws_router.add_websocket_route("/analytics", AnalyticsConsumer.as_asgi())

app.mount("/ws", ws_router)
