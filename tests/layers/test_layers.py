import pytest
from fast_channels.layers import (
    BaseChannelLayer,
    InMemoryChannelLayer,
)


@pytest.mark.asyncio
async def test_send_receive():
    layer = InMemoryChannelLayer()
    message = {"type": "test.message"}
    await layer.send("test.channel", message)
    assert message == await layer.receive("test.channel")


@pytest.mark.parametrize(
    "method",
    [
        BaseChannelLayer().require_valid_channel_name,
        BaseChannelLayer().require_valid_group_name,
    ],
)
@pytest.mark.parametrize(
    "channel_name,expected_valid",
    [("¯\\_(ツ)_/¯", False), ("chat", True), ("chat" * 100, False)],
)
def test_channel_and_group_name_validation(method, channel_name, expected_valid):
    if expected_valid:
        method(channel_name)
    else:
        with pytest.raises(TypeError):
            method(channel_name)


@pytest.mark.parametrize(
    "name",
    [
        "a" * 101,  # Group name too long
    ],
)
def test_group_name_length_error_message(name):
    """
    Ensure the correct error message is raised when group names
    exceed the character limit or contain invalid characters.
    """
    layer = BaseChannelLayer()
    expected_error_message = layer.invalid_name_error.format("Group")

    with pytest.raises(TypeError, match=expected_error_message):
        layer.require_valid_group_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "a" * 101,  # Channel name too long
    ],
)
def test_channel_name_length_error_message(name):
    """
    Ensure the correct error message is raised when group names
    exceed the character limit or contain invalid characters.
    """
    layer = BaseChannelLayer()
    expected_error_message = layer.invalid_name_error.format("Channel")

    with pytest.raises(TypeError, match=expected_error_message):
        layer.require_valid_channel_name(name)
