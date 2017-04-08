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
      "DEVICES": [
        {
          "port": 12340,
          "on_cmd": "http://192.168.1.3/myserver/switches/1/on",
          "off_cmd": "http://192.168.1.3/myserver/switches/1/off",
          "method": "GET",
          "name": "fake switch one"
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
    requests==2.13.0
"""

from functools import partialmethod  # type: ignore

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

    def __init__(self, name: str, port: int, on_cmd: str, off_cmd: str,
                 method: str="GET", on_data: dict=None, off_data: dict=None,
                 on_json: dict=None, off_json: dict=None, headers: dict=None,
                 auth_type: str=None, user: str=None, password: str=None) \
            -> None:

        """Initialize a RESTAPIPlugin instance

        Args:
            on_cmd: URL to be called when turning device on
            off_cmd: URL to be called when turning device off
            method: HTTP method to be used for both `on()` and `off()`
            on_data: HTTP body to turn device on
            off_data: HTTP body to turn device off
            on_json: JSON body to turn device on
            off_json: JSON body to turn device off
            headers: Additional headers for both `on()` and `off()`
            auth_type: Either `basic` or `digest` if needed
            user: Username for `auth`
            password: Password for `auth`
       """

        self.method = method
        self.headers = headers
        self.auth = None  # type: Union[HTTPBasicAuth, HTTPDigestAuth]

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

        self.on_data = on_data
        self.off_data = off_data

        self.on_json = on_json
        self.off_json = off_json

        if auth_type:
            if auth_type.lower() == "basic":
                self.auth = HTTPBasicAuth(user, password)

            elif auth_type.lower() == "digest":
                self.auth = HTTPDigestAuth(user, password)

        super().__init__(name=name, port=port)

    def set_state(self, cmd: str, data: str, json: str) -> bool:
        """Call HTTP method, for use by `functools.partialmethod`."""

        r = requests.request(self.method, getattr(self, cmd),
                             data=getattr(self, data),
                             json=getattr(self, json), headers=self.headers,
                             auth=self.auth)
        return r.status_code in [200, 201]

    on = partialmethod(set_state, 'on_cmd', 'on_data', 'on_json')
    off = partialmethod(set_state, 'off_cmd', 'off_data', 'off_json')
