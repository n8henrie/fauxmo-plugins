"""Fauxmo plugin to interact with Home Assistant devices.

Install to Fauxmo by downloading or cloning and including in your Fauxmo
config.
Example config:
```
{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "HomeAssistantPlugin": {
            "ha_host": "192.168.0.50",
            "ha_port": 8123,
            "ha_token": "abc123",
            "path": "/path/to/Home Assistantapiplugin.py",
            "DEVICES": [
                {
                    "name": "example Home Assistant device 1",
                    "port": 12345,
                    "entity_id": "switch.my_fake_switch"
                },
                {
                    "name": "example Home Assistant device 2",
                    "port": 12345,
                    "entity_id": "cover.my_fake_cover"
                }
            ]
        }
    }
}
```
"""

import json

from fauxmo.plugins import FauxmoPlugin
from requests import get, post


class HomeAssistantPlugin(FauxmoPlugin):
    """Fauxmo Plugin for Home Assistant REST API.

    Allows users to specify Home Assistant services in their config.json and
    toggle these with the Echo.
    """

    service_map = {
        'cover': {
            'on': 'open_cover',
            'off': 'close_cover',
            'on_state': 'open',
            'off_state': 'closed',
        },
        'homeassistant': {
            'on': 'turn_on',
            'off': 'turn_off',
        },
        'light': {
            'on': 'turn_on',
            'off': 'turn_off',
        },
        'media_player': {
            'on': 'turn_on',
            'off': 'turn_off',
        },
        'switch': {
            'on': 'turn_on',
            'off': 'turn_off',
        },
    }

    def __init__(self, name: str, port: int, entity_id: str, ha_host: str,
                 ha_token: str = None, ha_port: int = 8123) -> None:
        """Initialize a HomeAssistantPlugin instance.

        Args:
            ha_host: IP address of device running Home Assistant
            ha_token: long lived Home Assistant token
            entity_id: `entity_id` used by Home Assistant,
                       one easy way to find is to
                       curl and grep the REST API, eg:
                       `curl http://IP/api/bootstrap | grep entity_id`
            ha_port: Port running Home Assistant
                     on the host computer (default 8123)
        """
        self.ha_host = ha_host
        self.ha_token = ha_token
        self.entity_id = entity_id
        self.ha_port = ha_port

        self.domain = self.entity_id.split(".")[0]
        if self.domain == 'group':
            self.domain = 'homeassistant'

        super().__init__(name=name, port=port)

    def send(self, signal: str) -> bool:
        """Send the updated state to Home Assistant.

        Args:
            signal (const): the state to change to; see service_map
        """
        url = 'http://' + self.ha_host + ':' + str(self.ha_port) + \
              '/api/services/' + self.domain + '/' + signal
        headers = {
            'Authorization': 'Bearer ' + str(self.ha_token),
            'content-type': 'application/json',
        }
        data = {'entity_id': self.entity_id}

        response = post(
            url,
            headers=headers,
            data=str.encode(json.dumps(data))
        )
        return response.status_code == 200

    def on(self) -> bool:
        """Turn the Home Assistant device on.

        Returns:
            Whether the device seems to have been turned on.

        """
        on_cmd = HomeAssistantPlugin.service_map[self.domain.lower()]['on']
        return self.send(on_cmd)

    def off(self) -> bool:
        """Turn the Home Assistant device off.

        Returns:
            Whether the device seems to have been turned off.

        """
        off_cmd = HomeAssistantPlugin.service_map[self.domain.lower()]['off']
        return self.send(off_cmd)

    def get_state(self) -> str:
        """Query the state of the Home Assistant device."""
        url = 'http://' + self.ha_host + ':' + str(self.ha_port) + \
              '/api/states/' + self.entity_id
        headers = {
            'Authorization': 'Bearer ' + str(self.ha_token),
            'content-type': 'application/json',
        }

        response = get(url, headers=headers)
        return json.loads(response.text)['state']
