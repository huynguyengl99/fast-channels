from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from sandbox.consumer import (
    AnalyticsConsumer,
    ChatConsumer,
    NotificationConsumer,
    ReliableChatConsumer,
    SystemMessageConsumer,
)
from sandbox.layers import setup_layers

setup_layers()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="sandbox/static"), name="static")

# ----------------- HTML Client -----------------
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Chat Demo</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h1>WebSocket Chat Demo</h1>
        <button class="analytics-btn" onclick="sendAnalyticsEvent()">Send Analytics Event</button>

        <div class="chat-container">
            <div class="chat-box system-chat">
                <h3>System Messages (No Layer)</h3>
                <form class="input-form" onsubmit="sendSystemMessage(event)">
                    <input type="text" id="systemMessageText" placeholder="Type system message..." autocomplete="off"/>
                    <button type="submit">Send</button>
                </form>
                <ul id='systemMessages' class='messages'></ul>
            </div>

            <div class="chat-box regular-chat">
                <h3>Regular Chat (With Layers)</h3>
                <form class="input-form" onsubmit="sendMessage(event)">
                    <input type="text" id="messageText" placeholder="Type message..." autocomplete="off"/>
                    <button type="submit">Send</button>
                </form>
                <ul id='messages' class='messages'></ul>
            </div>
        </div>
        <script>
            // WebSocket connections for different layer types
            var wsChat = new WebSocket("ws://localhost:8080/ws/chat");
            var wsNotifications = new WebSocket("ws://localhost:8080/ws/notifications");
            var wsReliable = new WebSocket("ws://localhost:8080/ws/reliable");
            var wsAnalytics = new WebSocket("ws://localhost:8080/ws/analytics");
            var wsSystem = new WebSocket("ws://localhost:8080/ws/system");

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

            // Handle analytics messages
            wsAnalytics.onmessage = function(event) {
                addMessage("Analytics: " + event.data, "analytics");
            };

            // Handle system messages
            wsSystem.onmessage = function(event) {
                addSystemMessage(event.data);
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

            function addSystemMessage(text, isUserMessage = false) {
                var messages = document.getElementById('systemMessages');
                var message = document.createElement('li');
                message.className = isUserMessage ? 'user-message' : 'system';
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

            function sendSystemMessage(event) {
                var input = document.getElementById("systemMessageText");
                var message = input.value;

                if (message.trim() === '') return;

                // Show user message first
                addSystemMessage("👤 User: " + message, true);

                // Send to system WebSocket connection
                if (wsSystem.readyState === WebSocket.OPEN) {
                    wsSystem.send(message);
                }

                input.value = '';
                event.preventDefault();
            }

            function sendAnalyticsEvent() {
                if (wsAnalytics.readyState === WebSocket.OPEN) {
                    var event = {
                        type: "page_view",
                        timestamp: new Date().toISOString(),
                        user_agent: navigator.userAgent,
                        url: window.location.href
                    };
                    wsAnalytics.send(JSON.stringify(event));
                }
            }

            // Send analytics event on page load
            window.onload = function() {
                setTimeout(function() {
                    sendAnalyticsEvent();
                }, 1000); // Wait 1 second for connection
            };
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
ws_router.add_websocket_route("/system", SystemMessageConsumer.as_asgi())

app.mount("/ws", ws_router)
