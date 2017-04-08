"""test_commandlineplugin.py :: Tests for Fauxmo's `CommandLinePlugin`.

For testing purposes, `on_cmd`s will run without error (return code 0) and
`off_cmd`s will have a return code other than 0 and therefore return False. """

import json

from commandlineplugin import CommandLinePlugin

import pytest
import requests


config_path_str = "tests/test_commandlineplugin_config.json"


def test_commandlineplugin_integration(fauxmo_server: pytest.fixture) -> None:
    """Test "on" and "off" actions for CommandLinePlugin

    This test uses requests to `post` a value to a Fauxmo device that
    simulates the way the Echo interacts with the Fauxmo server when it gets a
    request to turn something `on` or `off`.
    """

    data_template = '<BinaryState>{}</BinaryState>'.format
    data_on = data_template(1)
    data_off = data_template(0)

    with fauxmo_server(config_path_str) as fauxmo_ip:
        base_url = f'http://{fauxmo_ip}:12345/upnp/control/basicevent1'
        resp_on = requests.post(base_url, data=data_on)
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(base_url, data=data_off)
    assert resp_on.status_code == 200


def test_commandlineplugin_unit() -> None:
    """Simpler unit tests on just the device without the integration"""
    with open(config_path_str) as f:
        config = json.load(f)  # type: dict

    for device in config["PLUGINS"]["CommandLinePlugin"]["DEVICES"]:
        assert CommandLinePlugin(**device).on() is True
        assert CommandLinePlugin(**device).off() is False
