"""test_restapiplugin.py :: Tests for Fauxmo's `RESTAPIPlugin`."""

import json
import time
from unittest.mock import MagicMock, patch

from mqttplugin import MQTTPlugin

config_path_str = "tests/test_mqttplugin_config.json"


def test_mqttplugin_mosquitto_dot_org() -> None:
    """Test MQTTPlugin against test.mosquitto.org."""
    with open(config_path_str) as f:
        config: dict = json.load(f)

    mosquitto_devices = (
        device
        for device in config["PLUGINS"]["MQTTPlugin"]["DEVICES"]
        if device["mqtt_server"] == "test.mosquitto.org"
    )
    for device_conf in mosquitto_devices:
        device = MQTTPlugin(**device_conf)

        for _ in range(100):
            if device.subscribed is True:
                break
            time.sleep(0.1)
        else:
            assert False, "Time out waiting for subscribe."

        assert device.on() is True
        for _ in range(20):
            state = device.get_state()
            if state != "unknown":
                break
            time.sleep(0.1)
        assert state == "on"

        assert device.off() is True
        for _ in range(20):
            state = device.get_state()
            if state != "on":
                break
            time.sleep(0.1)
        assert state == "off"


@patch("mqttplugin.Client", autospec=True)
def test_mqtt_auth(mock_client: MagicMock) -> None:
    """Ensure auth is being used if available."""
    mock_instance = mock_client.return_value
    with open(config_path_str) as f:
        config: dict = json.load(f)

    device_conf = next(
        device
        for device in config["PLUGINS"]["MQTTPlugin"]["DEVICES"]
        if device["mqtt_server"] == "mqtt.yes_auth.no_state"
    )
    MQTTPlugin(**device_conf)
    mock_instance.username_pw_set.assert_called_once_with(
        "MyUser", "MyPassword"
    )


@patch("mqttplugin.Client", autospec=True)
def test_mqtt_nostate(mock_client: MagicMock) -> None:
    """If state_cmd is not specified, loop_start is not called."""
    mock_instance = mock_client.return_value
    with open(config_path_str) as f:
        config: dict = json.load(f)

    device_conf = next(
        device
        for device in config["PLUGINS"]["MQTTPlugin"]["DEVICES"]
        if device["mqtt_server"] == "mqtt.yes_auth.no_state"
    )
    device = MQTTPlugin(**device_conf)
    mock_instance.loop_start.assert_not_called()
    mock_instance.subscribe.assert_not_called()
    assert device.subscribed is False


@patch("mqttplugin.Client", autospec=True)
def test_mqtt_noauth(mock_client: MagicMock) -> None:
    """Ensure auth is not being used if not configured."""
    mock_instance = mock_client.return_value
    with open(config_path_str) as f:
        config: dict = json.load(f)

    device_conf = next(
        device
        for device in config["PLUGINS"]["MQTTPlugin"]["DEVICES"]
        if device["mqtt_server"] == "mqtt.no_auth.yes_state"
    )
    MQTTPlugin(**device_conf)
    mock_instance.username_pw_set.assert_not_called()


@patch("mqttplugin.Client", autospec=True)
def test_mqtt_clientid(mock_client: MagicMock) -> None:
    """Ensure mqtt client id is properly set when configured."""
    with open(config_path_str) as f:
        config: dict = json.load(f)

    device_conf = next(
        device
        for device in config["PLUGINS"]["MQTTPlugin"]["DEVICES"]
        if device["mqtt_client_id"]
    )
    MQTTPlugin(**device_conf)
    mock_client.assert_called_once_with(
        client_id=device_conf["mqtt_client_id"]
    )
