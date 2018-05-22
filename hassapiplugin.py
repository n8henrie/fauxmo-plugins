"""Fauxmo plugin to interact with HomeAssistant (hass) devices.

Install to Fauxmo by downloading or cloning and including in your Fauxmo
config. NB: For all Fauxmo plugins you must **manually** install any
required 3rd party modules (e.g. `homeassistant`) -- make sure you install
them where Fauxmo can find them (i.e. the same virtualenv).

Example config:

    def __init__(self, name: str, port: int, hass_host: str, hass_password:
                 str, entity_id: str, hass_port: int=8123) -> None:
```
{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "HassAPIPlugin": {
            "hass_host": "192.168.0.50",
            "hass_port": 8123,
            "hass_password": "abc123",
            "path": "/path/to/hassapiplugin.py",
            "DEVICES": [
                {
                    "name": "example hass device 1",
                    "port": 12345,
                    "entity_id": "switch.my_fake_switch"
                },
                {
                    "name": "example hass device 2",
                    "port": 12345,
                    "entity_id": "cover.my_fake_cover"
                }
            ]
        }
    }
}
```

Dependencies:
    homeassistant==0.57.3
"""

from collections import defaultdict

import homeassistant.remote
from fauxmo.plugins import FauxmoPlugin
from homeassistant.const import (  # noqa
        SERVICE_TURN_ON, SERVICE_TURN_OFF,
        SERVICE_OPEN_COVER, SERVICE_CLOSE_COVER,
        STATE_OFF, STATE_ON,
        STATE_CLOSED, STATE_OPEN,
        )


class HassAPIPlugin(FauxmoPlugin):
    """Fauxmo Plugin for HomeAssistant (hass) Python API.

    Allows users to specify Home Assistant services in their config.json and
    toggle these with the Echo. While this can be done with Home Assistant's
    REST API as well (example included), I find it easier to use the Python
    API.
    """

    service_map = defaultdict(dict)
    service_map.update({
            'cover': {
                'on': SERVICE_OPEN_COVER,
                'off': SERVICE_CLOSE_COVER,
                'on_state': STATE_OPEN,
                'off_state': STATE_CLOSED,
                },
            })

    def __init__(self, name: str, port: int, hass_host: str, entity_id: str,
                 hass_password: str=None, hass_port: int=8123) -> None:
        """Initialize a HassAPIPlugin instance.

        Args:
            hass_host: IP address of device running Home Assistant
            password: Home Assistant password
            entity_id: `entity_id` used by hass, one easy way to find is to
                       curl and grep the REST API, eg:
                          `curl http://IP/api/bootstrap | grep entity_id`
            hass_port: Port running hass on the host computer (default 8123)
        """
        self.hass_host = hass_host
        self.hass_password = hass_password
        self.entity_id = entity_id
        self.hass_port = hass_port

        self.domain = self.entity_id.split(".")[0]
        if self.domain == 'group':
            self.domain = 'homeassistant'
        self.api = homeassistant.remote.API(host=self.hass_host,
                                            api_password=self.hass_password,
                                            port=self.hass_port)

        super().__init__(name=name, port=port)

    def send(self, signal: str) -> bool:
        """Send a signal to the hass `call_service` function, returns True.

        The hass Python API doesn't appear to return anything with this
        function, but will raise an exception if things didn't seem to work, so
        I have it set to just return True, hoping for an exception if there was
        a problem.

        Args:
            signal (const): signal imported from homeassistant.const. I have
            imported SERVICE_TURN_ON and SERVICE_TURN_OFF, make sure you import
            any others that you need.
        """
        homeassistant.remote.call_service(self.api, self.domain, signal,
                                          {'entity_id': self.entity_id})
        return True

    def on(self) -> bool:
        """Turn the hass device on.

        Returns:
            Whether the device seems to have been turned on.

        """
        on_cmd = (
                HassAPIPlugin
                .service_map[self.domain.lower()]
                .get('on', SERVICE_TURN_ON)
                 )
        return self.send(on_cmd)

    def off(self) -> bool:
        """Turn the hass device off.

        Returns:
            Whether the device seems to have been turned off.

        """
        off_cmd = (
                HassAPIPlugin
                .service_map[self.domain.lower()]
                .get('off', SERVICE_TURN_OFF)
                 )
        return self.send(off_cmd)

    def get_state(self) -> str:
        """Query the state of the hass device."""
        smap = HassAPIPlugin.service_map[self.domain.lower()]
        response = homeassistant.remote.get_state(self.api, self.entity_id)

        # If no custom `on_state` key is set default to `STATE_ON`
        if response.state == smap.get('on_state', STATE_ON):
            return 'on'
        elif response.state == smap.get('off_state', STATE_OFF):
            return 'off'
        return 'unknown'
