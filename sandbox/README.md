# FastAPI WebSocket Chat Demo - Sandbox Application

A complete real-time WebSocket chat application demonstrating all key features of fast-channels. This sandbox provides both a working implementation and tutorial templates for learning.

## 🚀 Quick Start

### Option 1: Run the Complete Demo

```bash
# Start Redis (required for channel layers and background jobs)
docker compose up -d

# Start both FastAPI app and RQ worker
python sandbox/start_dev.py
```

Visit **http://localhost:8080** to see the complete application in action!

### Option 2: Learn Step-by-Step

Use the tutorial files to build the application yourself:

```bash
# Copy tutorial files to start fresh
cp -r sandbox/tutorial/ my-chat-app/
cd my-chat-app/

# Follow the tutorial documentation
# See: https://fast-channels.readthedocs.io/en/latest/tutorial/
```

## 📱 Features Demonstrated

The sandbox showcases 4 different WebSocket communication patterns:

### 1. **System Messages** (Direct WebSocket)
- Simple echo server without channel layers
- Direct client-server communication
- Perfect for basic real-time features

### 2. **Room Chat** (Dynamic Groups)
- Multi-room chat with dynamic connections
- Users can join/leave specific rooms
- Demonstrates channel layer group messaging

### 3. **Background Job Processing** (RQ Integration)
- Real background job processing with Redis Queue (RQ)
- Multiple job types: translation, analysis, AI generation
- Async job queueing with real-time result delivery

### 4. **Showcase** (Multiple Layer Types)
- Multiple channel layers working together
- Analytics events, notifications, reliable messaging
- Advanced patterns and external integrations

## 🏗️ Architecture

### Directory Structure

```
sandbox/
├── main.py                    # Complete FastAPI application
├── start_dev.py              # Development startup script (app + worker)
├── worker.py                 # RQ background job worker
├── tasks.py                  # Background job definitions
├── layers.py                 # Channel layer configuration
├── apps/                     # Modular consumer apps
│   ├── system_chat/          # Direct WebSocket consumer
│   ├── room_chat/            # Room-based chat consumer
│   ├── background_jobs/      # Job processing consumer
│   └── showcase/             # Multi-layer demo consumers
├── static/
│   ├── css/style.css         # Application styling
│   └── js/main.js            # Single JavaScript file with all functionality
└── tutorial/                 # Tutorial template files
    ├── main.py               # Tutorial starting point
    └── apps/                 # Consumer templates with TODOs
```

### Technology Stack

- **FastAPI** - ASGI web framework for WebSocket handling
- **fast-channels** - Channel layers and consumer patterns
- **Redis** - Channel layer backend and job queue
- **RQ (Redis Queue)** - Background job processing
- **Vanilla JavaScript** - Client-side WebSocket handling

## 🔧 Development Features

### Background Job Processing

The sandbox includes a complete background job system:

- **Real job queue** using RQ (Redis Queue)
- **Multiple job types** with different processing times
- **Worker process** that runs alongside the web app
- **Real-time results** delivered via WebSocket

Example job types:
- `translate` - Mock translation service (2s delay)
- `analyze` - Text analysis with statistics (3s delay)
- `generate` - AI response generation (4s delay)
- `default` - Simple text processing (1s delay)

### Channel Layer Configuration

Multiple channel layers for different use cases:

```python
# In layers.py
CHANNEL_LAYERS = {
    "chat": RedisChannelLayer(...),           # Basic group messaging
    "queue": RedisChannelLayer(...),          # Reliable delivery
    "notifications": RedisChannelLayer(...),  # Real-time notifications
    "analytics": RedisChannelLayer(...)       # Analytics events
}
```

### Modular Consumer Architecture

Each feature is implemented as a separate app:

- **Focused learning** - Study one pattern at a time
- **Clear separation** - Different consumers for different purposes
- **Reusable code** - Copy patterns to your own projects
- **Tutorial ready** - Templates with extensive TODO comments

## 🎓 Learning Path

### For Beginners
1. Start with **System Messages** (direct WebSocket)
2. Add **Room Chat** (channel layers + groups)
3. Explore **Background Jobs** (async processing)
4. Study **Showcase** (advanced patterns)

### For Advanced Users
- Examine consumer implementations in `apps/`
- Study channel layer configurations in `layers.py`
- Review background job patterns in `tasks.py`
- Analyze JavaScript integration in `static/js/main.js`

## 🚀 Production Considerations

This sandbox demonstrates patterns suitable for production:

### Scalability
- **Channel layers** enable horizontal scaling
- **Background workers** can run on separate machines
- **Redis** provides reliable message delivery
- **Modular design** supports microservice architecture

### Monitoring
- **Job status tracking** through RQ
- **WebSocket connection management**
- **Error handling and recovery**
- **Logging and debugging support**

### Security
- **Input validation** in consumers
- **Rate limiting** considerations
- **Authentication/authorization** patterns
- **CORS and WebSocket security**

## 📚 Related Documentation

- **Tutorial**: [Step-by-step guide](https://fast-channels.readthedocs.io/en/latest/tutorial/)
- **Concepts**: [Understanding channel layers](https://fast-channels.readthedocs.io/en/latest/concepts/)
- **API Reference**: [Consumer and layer APIs](https://fast-channels.readthedocs.io/en/latest/api/)
- **Examples**: [More usage patterns](https://fast-channels.readthedocs.io/en/latest/examples/)

## 🤝 Contributing

Found a bug or want to improve the sandbox? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This sandbox application is part of the fast-channels project and follows the same license terms.
