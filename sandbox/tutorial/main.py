"""
FastAPI WebSocket Chat Demo - Template Base

This template provides a starting point for building WebSocket chat applications
with fast-channels. Follow the comments to add your own consumers and features.
"""

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# TODO: Import your consumers here (uncomment as needed)
# from sandbox.apps.system_chat.consumer import SystemMessageConsumer
# from sandbox.apps.room_chat.consumer import RoomChatConsumer
# from sandbox.apps.background_jobs.consumer import BackgroundJobConsumer
# from sandbox.apps.showcase.consumer import (
#     AnalyticsConsumer,
#     ChatConsumer,
#     NotificationConsumer,
#     ReliableChatConsumer,
# )

# TODO: Import and setup your channel layers
# from sandbox.layers import setup_layers
# setup_layers()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="sandbox/static"), name="static")

# ----------------- HTML Client -----------------
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Chat Demo</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <h1>WebSocket Chat Demo</h1>
        <button class="analytics-btn" onclick="sendAnalyticsEvent()">Send Analytics Event</button>

        <div class="chat-container">
            <!-- System Messages Chat Box -->
            <div class="chat-box system-chat">
                <h3>System Messages (No Layer)</h3>
                <form class="input-form" onsubmit="sendSystemMessage(event)">
                    <input type="text" id="systemMessageText" placeholder="Type system message..." autocomplete="off"/>
                    <button type="submit">Send</button>
                </form>
                <ul id='systemMessages' class='messages'></ul>
            </div>

            <!-- Room Chat Box -->
            <div class="chat-box room-chat">
                <h3>Room Chat</h3>
                <div class="room-controls">
                    <input type="text" id="roomName" placeholder="Enter room name..." autocomplete="off"/>
                    <button onclick="connectToRoom()" id="connectBtn">Connect</button>
                    <button onclick="disconnectFromRoom()" id="disconnectBtn" style="display:none;">Disconnect</button>
                </div>
                <div id="currentRoom" style="margin: 10px 0; font-weight: bold;"></div>
                <form class="input-form" onsubmit="sendRoomMessage(event)">
                    <input type="text" id="roomMessageText" placeholder="Type room message..." autocomplete="off" disabled/>
                    <button type="submit" disabled>Send</button>
                </form>
                <ul id='roomMessages' class='messages'></ul>
            </div>

            <!-- Background Job Processing Chat Box -->
            <div class="chat-box job-chat">
                <h3>Background Job Processing</h3>
                <div class="job-controls">
                    <select id="jobType">
                        <option value="default">Default Processing</option>
                        <option value="translate">Translation</option>
                        <option value="analyze">Text Analysis</option>
                        <option value="generate">AI Generation</option>
                    </select>
                </div>
                <form class="input-form" onsubmit="sendJobMessage(event)">
                    <input type="text" id="jobMessageText" placeholder="Type message for processing..." autocomplete="off"/>
                    <button type="submit">Process</button>
                </form>
                <ul id='jobMessages' class='messages'></ul>
            </div>

            <!-- All Layers Combination Chat Box -->
            <div class="chat-box regular-chat">
                <h3>Showcase</h3>
                <form class="input-form" onsubmit="sendMessage(event)">
                    <input type="text" id="messageText" placeholder="Type message..." autocomplete="off"/>
                    <button type="submit">Send</button>
                </form>
                <ul id='messages' class='messages'></ul>
            </div>
        </div>

        <script src="/static/js/main.js"></script>
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

# TODO: Add your WebSocket routes here
# Example routes:
# ws_router.add_websocket_route("/system", SystemMessageConsumer.as_asgi())
# ws_router.add_websocket_route("/room/{room_name}", RoomChatConsumer.as_asgi())
# ws_router.add_websocket_route("/backgroundjob", BackgroundJobConsumer.as_asgi())
# ws_router.add_websocket_route("/chat", ChatConsumer.as_asgi())
# ws_router.add_websocket_route("/reliable", ReliableChatConsumer.as_asgi())
# ws_router.add_websocket_route("/notifications", NotificationConsumer.as_asgi())
# ws_router.add_websocket_route("/analytics", AnalyticsConsumer.as_asgi())

app.mount("/ws", ws_router)
