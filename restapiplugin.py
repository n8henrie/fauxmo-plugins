"""restapiplugin.py

Fauxmo plugin that provides access to services exposing a REST API.

Uses `requests` for a simpler api.

Example config:

```
{
  "FAUXMO": {
    "ip_address": "auto"
  },
  "PLUGINS": {
    "RESTAPIPlugin": {
      "path": "/path/to/restapiplugin.py",
      "DEVICES": [
        {
          "port": 12340,
          "on_cmd": "http://192.168.1.3/myserver/switches/1/on",
          "off_cmd": "http://192.168.1.3/myserver/switches/1/off",
          "method": "GET",
          "name": "fake switch one",
          "state_cmd": "http://192.168.1.3/myserver/switches/1/state",
          "state_method": "GET",
          "state_response_on": "<p>Your switch is on."</p>"
          "state_response_off": "<p>Your switch is off.</p>"
        },
        {
          "port": 12341,
          "on_cmd": "http://localhost:54321/devices/garage%20light",
          "off_cmd": "http://localhost:54321/devices/garage%20light",
          "on_data": {"isOn": 1},
          "off_data": {"isOn": 0},
          "user": "this",
          "password": "that",
          "method": "PUT",
          "name": "fake Indigo switch"
        },
        {
          "name": "home assistant switch by REST API",
          "port": 12342,
          "on_cmd": "http://192.168.1.4:8123/api/services/switch/turn_on",
          "off_cmd": "http://192.168.1.4:8123/api/services/switch/turn_off",
          "method": "POST",
          "headers": {"x-ha-access": "your_hass_password"},
          "on_data": {"entity_id": "switch.fake_hass_switch"},
          "off_data": {"entity_id": "switch.fake_hass_switch"}
        }
      ]
    }
  }
}
```

Dependencies:
    requests==2.18.4
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from typing import Union  # noqa

from fauxmo.plugins import FauxmoPlugin


class RESTAPIPlugin(FauxmoPlugin):
    """REST API plugin class.

    The Fauxmo class expects plugins to be instances of objects that have on()
    and off() methods that return True on success and False otherwise. This
    class takes a mix of url, method, header, body, and auth data and makes
    REST calls to a device.
    """

    def __init__(
            self,
            *,
            auth_type: str = None,
            headers: dict = None,
            method: str = "GET",
            name: str,
            off_cmd: str,
            off_data: dict = None,
            off_json: dict = None,
            on_cmd: str,
            on_data: dict = None,
            on_json: dict = None,
            password: str = None,
            port: int,
            state_cmd: str = None,
            state_data: dict = None,
            state_json: dict = None,
            state_method: str = "GET",
            state_response_off: str = None,
            state_response_on: str = None,
            user: str=None,
            ) -> None:

        """Initialize a RESTAPIPlugin instance

        Args:
            auth_type: Either `basic` or `digest` if needed
            headers: Additional headers for both `on()` and `off()`
            method: HTTP method to be used for both `on()` and `off()`
            off_cmd: URL to be called when turning device off
            off_data: HTTP body to turn device off
            off_json: JSON body to turn device off
            on_cmd: URL to be called when turning device on
            on_data: HTTP body to turn device on
            on_json: JSON body to turn device on
            password: Password for `auth`
            state_cmd: URL to be called to determine device state
            state_data: Optional POST data to query device state
            state_json: Optional json data to query device state
            state_method: HTTP method to be used for `get_state()`
            state_response_off: If this string is in the response to state_cmd,
                                the device is off.
            state_response_on: If this string is in the response to state_cmd,
                               the device is on.
            user: Username for `auth`
       """

        self.method = method
        self.state_method = state_method
        self.headers = headers
        self.auth: Union[HTTPBasicAuth, HTTPDigestAuth] = None

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.state_cmd = state_cmd

        self.on_data = on_data
        self.off_data = off_data
        self.state_data = state_data

        self.on_json = on_json
        self.off_json = off_json
        self.state_json = state_json

        self.state_response_on = state_response_on
        self.state_response_off = state_response_off

        if auth_type:
            if auth_type.lower() == "basic":
                self.auth = HTTPBasicAuth(user, password)

            elif auth_type.lower() == "digest":
                self.auth = HTTPDigestAuth(user, password)

        super().__init__(name=name, port=port)

    def on(self) -> bool:
        """Turn device on."""
        return self.set_state(self.on_cmd, self.on_data, self.on_json)

    def off(self) -> bool:
        """Turn device off."""
        return self.set_state(self.off_cmd, self.off_data, self.off_json)

    def set_state(self, cmd: str, data: dict, json: dict) -> bool:
        """Call HTTP method via Requests."""

        r = requests.request(self.method, cmd, data=data, json=json,
                             headers=self.headers, auth=self.auth)
        return r.status_code in [200, 201]

    def get_state(self) -> str:
        """Get device state.

        Returns:
            "on", "off", or "unknown"

        """
        if self.state_cmd is None:
            return "unknown"

        resp = requests.request(self.state_method, self.state_cmd,
                                data=self.state_data, json=self.state_json,
                                headers=self.headers, auth=self.auth)

        if self.state_response_off in resp.text:
            return "off"
        elif self.state_response_on in resp.text:
            return "on"
        return "unknown"
