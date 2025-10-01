// FastAPI WebSocket Chat Demo - Main JavaScript
// All functionality combined in a single file for simplicity

// =============================================================================
// WebSocket Connections
// =============================================================================

// WebSocket connections for different layer types
var wsChat = new WebSocket("ws://localhost:8080/ws/chat");
var wsNotifications = new WebSocket("ws://localhost:8080/ws/notifications");
var wsReliable = new WebSocket("ws://localhost:8080/ws/reliable");
var wsAnalytics = new WebSocket("ws://localhost:8080/ws/analytics");
var wsSystem = new WebSocket("ws://localhost:8080/ws/system");
var wsBackgroundJob = new WebSocket("ws://localhost:8080/ws/backgroundjob");
var wsRoom = null; // Dynamic room connection

// =============================================================================
// WebSocket Event Handlers
// =============================================================================

// Handle chat messages
wsChat.onmessage = function(event) {
    addMessage("Chat: " + event.data, "chat");
};

// Handle notifications (JSON format)
wsNotifications.onmessage = function(event) {
    try {
        var data = JSON.parse(event.data);
        addMessage("Notification: " + data.message, "notification");
    } catch (e) {
        // Fallback for non-JSON messages
        addMessage("Notification: " + event.data, "notification");
    }
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

// Handle background job messages (JSON format)
wsBackgroundJob.onmessage = function(event) {
    try {
        var data = JSON.parse(event.data);
        var message = data.message || event.data;

        // Add status indicator for different types of responses
        if (data.status === "queuing") {
            addJobMessage("⏳ " + message);
        } else if (data.status === "queued") {
            addJobMessage("📋 " + message + " (ID: " + data.job_id + ")");
        } else if (data.status === "error") {
            addJobMessage("❌ " + message);
        } else if (data.type === "job_result") {
            addJobMessage("✅ " + message);
        } else {
            addJobMessage(message);
        }
    } catch (e) {
        // Fallback for non-JSON messages
        addJobMessage(event.data);
    }
};

// =============================================================================
// Utility Functions - Message Display
// =============================================================================

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

function addRoomMessage(text) {
    var messages = document.getElementById('roomMessages');
    var message = document.createElement('li');
    message.className = 'room';
    var content = document.createTextNode(text);
    message.appendChild(content);
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}

function addJobMessage(text) {
    var messages = document.getElementById('jobMessages');
    var message = document.createElement('li');
    message.className = 'job';
    var content = document.createTextNode(text);
    message.appendChild(content);
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}

// =============================================================================
// System Chat Functions
// =============================================================================

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

// =============================================================================
// Room Chat Functions
// =============================================================================

function connectToRoom() {
    var roomName = document.getElementById("roomName").value.trim();
    if (roomName === '') {
        alert('Please enter a room name');
        return;
    }

    // Close existing room connection if any
    if (wsRoom) {
        wsRoom.close();
    }

    // Create new room WebSocket connection
    wsRoom = new WebSocket("ws://localhost:8080/ws/room/" + roomName);

    wsRoom.onopen = function() {
        document.getElementById("currentRoom").textContent = "Connected to room: " + roomName;
        document.getElementById("connectBtn").style.display = "none";
        document.getElementById("disconnectBtn").style.display = "inline";
        document.getElementById("roomMessageText").disabled = false;
        document.querySelector("#roomMessageText").nextElementSibling.disabled = false;
    };

    wsRoom.onmessage = function(event) {
        addRoomMessage(event.data);
    };

    wsRoom.onclose = function() {
        document.getElementById("currentRoom").textContent = "";
        document.getElementById("connectBtn").style.display = "inline";
        document.getElementById("disconnectBtn").style.display = "none";
        document.getElementById("roomMessageText").disabled = true;
        document.querySelector("#roomMessageText").nextElementSibling.disabled = true;
    };
}

function disconnectFromRoom() {
    if (wsRoom) {
        wsRoom.close();
        wsRoom = null;
    }
}

function sendRoomMessage(event) {
    var input = document.getElementById("roomMessageText");
    var message = input.value;

    if (wsRoom && wsRoom.readyState === WebSocket.OPEN && message.trim() !== '') {
        wsRoom.send(message);
    }

    input.value = '';
    event.preventDefault();
}

// =============================================================================
// Background Jobs Functions
// =============================================================================

function sendJobMessage(event) {
    var input = document.getElementById("jobMessageText");
    var message = input.value;
    var jobType = document.getElementById("jobType").value;

    if (message.trim() === '') return;

    if (wsBackgroundJob.readyState === WebSocket.OPEN) {
        // Send structured message for different job types
        var jobData = {
            type: jobType,
            content: message
        };
        wsBackgroundJob.send(JSON.stringify(jobData));
    }

    input.value = '';
    event.preventDefault();
}

// =============================================================================
// Showcase Functions (All Layers)
// =============================================================================

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

// =============================================================================
// Analytics Functions
// =============================================================================

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

// =============================================================================
// Initialization
// =============================================================================

// Send analytics event on page load
window.onload = function() {
    setTimeout(function() {
        sendAnalyticsEvent();
    }, 1000); // Wait 1 second for connection
};
