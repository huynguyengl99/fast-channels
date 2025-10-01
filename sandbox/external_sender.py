"""
Example of sending messages to WebSocket groups from outside a consumer,
using centralized layer configuration from layers.py.
"""

import asyncio

from fast_channels.layers import get_channel_layer

from sandbox.layers import setup_layers

setup_layers()

chat_layer = get_channel_layer("chat")
queue_layer = get_channel_layer("queue")
notifications_layer = get_channel_layer("notifications")
analytics_layer = get_channel_layer("analytics")


async def send_chat_message():
    """
    Send a message to the chat room using the chat layer.
    """
    if not chat_layer:
        print("❌ No chat layer available!")
        return

    await chat_layer.group_send(
        "chat_room",
        {
            "type": "chat_message",
            "message": "🔔 System announcement: Welcome to the chat!",
        },
    )

    print("✅ Chat message sent!")


async def send_reliable_message():
    """
    Send a message using the queue-based layer for guaranteed delivery.
    """
    if not queue_layer:
        print("❌ No queue layer available!")
        return

    await queue_layer.group_send(
        "reliable_chat",
        {
            "type": "reliable_chat_message",
            "message": "🔒 Important: System maintenance scheduled for tonight",
        },
    )

    print("✅ Reliable message sent!")


async def send_notification():
    """
    Send a notification using the notifications layer.
    """
    if not notifications_layer:
        print("❌ No notifications layer available!")
        return

    await notifications_layer.group_send(
        "notifications",
        {
            "type": "notification_message",
            "data": {
                "type": "system",
                "message": "🚨 Alert: High CPU usage detected on server",
            },
        },
    )

    print("✅ Notification sent!")


async def send_analytics_event():
    """
    Send analytics events using the analytics layer.
    """
    if not analytics_layer:
        print("❌ No analytics layer available!")
        return

    # Send multiple analytics events
    events = [
        "user_login:john_doe",
        "page_view:/dashboard",
        "button_click:export_data",
        "session_duration:1234",
        "error:api_timeout",
    ]

    for event in events:
        await analytics_layer.group_send(
            "analytics", {"type": "analytics_message", "message": f"📊 Event: {event}"}
        )
        await asyncio.sleep(0.1)  # Small delay between events

    print(f"✅ Sent {len(events)} analytics events!")


async def send_to_multiple_layers():
    """
    Demonstrate sending to different layers for different purposes.
    """
    print("🚀 Broadcasting to multiple layers...")

    # Send to chat (fast pub/sub)
    if chat_layer:
        await chat_layer.group_send(
            "chat_room",
            {
                "type": "chat_message",
                "message": "💬 Multi-layer broadcast: Chat message",
            },
        )

    # Send to notifications (ephemeral)
    if notifications_layer:
        await notifications_layer.group_send(
            "notifications",
            {
                "type": "notification_message",
                "data": {
                    "type": "broadcast",
                    "message": "🔔 Multi-layer broadcast: Notification",
                },
            },
        )

    # Send to queue (reliable)
    if queue_layer:
        await queue_layer.group_send(
            "reliable_chat",
            {
                "type": "reliable_chat_message",
                "message": "📨 Multi-layer broadcast: Reliable message",
            },
        )

    print("✅ Multi-layer broadcast complete!")


async def periodic_announcements():
    """
    Send periodic announcements to different channels.
    """
    print("⏰ Starting periodic announcements...")

    for i in range(3):
        # Alternate between different layers
        if i % 2 == 0:
            layer = chat_layer
            group = "chat_room"
            message = f"⏰ Hourly chat announcement #{i+1}"
        else:
            layer = notifications_layer
            group = "notifications"
            message = f"🔔 System status update #{i+1}"

        if layer:
            if group == "chat_room":
                await layer.group_send(
                    group, {"type": "chat_message", "message": message}
                )
            else:  # notifications
                await layer.group_send(
                    group,
                    {
                        "type": "notification_message",
                        "data": {"type": "periodic", "message": message},
                    },
                )
            print(f"✅ Sent announcement #{i+1}")

        await asyncio.sleep(1)  # 1 second between announcements

    print("✅ Periodic announcements complete!")


async def main():
    """
    Run all external messaging examples.
    """
    print("=== External Messaging with Centralized Layers ===\n")

    # Import layers module to trigger setup

    examples = [
        ("Chat Message", send_chat_message),
        ("Reliable Message", send_reliable_message),
        ("Notification", send_notification),
        ("Analytics Events", send_analytics_event),
        ("Multi-layer Broadcast", send_to_multiple_layers),
        ("Periodic Announcements", periodic_announcements),
    ]

    for name, func in examples:
        print(f"🎯 Running: {name}")
        try:
            await func()
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
        print()  # Add spacing between examples
        await asyncio.sleep(0.5)  # Brief pause between examples

    print("=== All Examples Complete! ===")


if __name__ == "__main__":
    asyncio.run(main())
