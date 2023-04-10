"""
Fauxmo plugin that provides access to services exposing by Z-Wave REST API.

Tested on z-way v2.3.8 / SmartHomeUI v1.9.0.
For zway-server see https://z-wave.me/z-way/
See "Z-Way Essentials" doc for API details.
Added by Jorge Rivera in June 2019.

Uses `requests` for a simpler api.

Example config:
```
{
  "FAUXMO": {
    "ip_address": "auto"
  },
  "PLUGINS": {
      "ZwavePlugin": {
        "path": "/path/to/zwaveplugin.py",
        "zwave_host" : "localhost",
        "zwave_port" : "8083",
        "zwave_user" : "admin",
        "zwave_pass" : "your_pass",
        "fake_state" : false,
        "DEVICES": [
          {
              "name"     : "hall light",
              "device"   : "HTTP_Device_switchBinary_62",
              "port"     : 49918
          },
          {
              "name"     : "bath light",
              "device"   : "HTTP_Device_switchBinary_63",
              "port"     : 49919
          }
        ]
      }
  }
}
```

Dependencies:
    requests==2.28.2
"""

import requests
from fauxmo import logger
from fauxmo.plugins import FauxmoPlugin

ZwavePlugin_version = "v0.3"

response_ok = '{"data":null,"code":200,"message":"200 OK","error":null}'


class ZwavePlugin(FauxmoPlugin):
    """Fauxmo Plugin for Z-WAVE (zway-server) REST API.

    Allows users to specify Z-Wave services in their config.json and
    toggle these with the Echo. While this can be done with Z-Wave
    REST API as well (example included), I find it easier to use the Python
    API.

    """

    def __init__(
        self,
        *,
        name: str,
        port: int,
        device: str,
        zwave_host: str = "localhost",
        zwave_port: int = 8083,
        zwave_user: str = "admin",
        zwave_pass: str = None,
        fake_state: bool = False,
        state: str = "unknown",
    ) -> None:
        """Initialize a ZwaveAPIPlugin instance.

        Args:
            zwave_host: IP address or dns name of zway-server
            zwave_port: TCP port running zway-server (default 8083)
            zwave_user: Zwave user
            zwave_pass: Zwave user password
            fake_state: Set to true for it does not exec a query for status,
                        it returns the previous status stored
            state:      Initial device status

        """
        self.zwave_host = zwave_host
        self.zwave_port = zwave_port
        self.zwave_user = zwave_user
        self.zwave_pass = zwave_pass
        self.zwave_device = device
        self.fake_state = fake_state

        logger.info(
            f"ZwavePlugin: {ZwavePlugin_version} "
            + "name: {name} device: {device} "
            + "port: {port} fake_state: {fake_state}"
        )

        super().__init__(name=name, port=port)

    def _ZwaveCmd(self, cmd: str) -> bool:
        url = (
            "http://"
            + self.zwave_host
            + ":"
            + str(self.zwave_port)
            + "/ZAutomation/api/v1/devices/"
            + self.zwave_device
            + "/command/"
            + cmd
        )
        logger.info(f"ZwavePlugin: Getting {url} ")

        try:
            resp = requests.get(url, auth=(self.zwave_user, self.zwave_pass))
        except Exception as e:
            logger.error(f"ZwavePlugin: {e}")
            return False

        if resp.status_code == 200:
            if resp.text == response_ok:
                self.state = cmd
                return True

        logger.error(f"ZwavePlugin: {resp.status_code} {resp.text} ")
        return False

    def on(self) -> bool:
        """Run on command.

        Returns:
            True if command seems to have run without error.

        """
        return self._ZwaveCmd("on")

    def off(self) -> bool:
        """Run off command.

        Returns:
            True if command seems to have run without error.

        """
        return self._ZwaveCmd("off")

    def get_state(self) -> str:
        """Get device state.

        Returns:
            "on", "off", or "unknown"
            If fake_state is set to true, it does not exec a query for status,
            it returns the previous status stored.

        """
        if self.fake_state:
            logger.info(f"ZwavePlugin: return fake {self.state} ")
            return self.state

        url = (
            "http://"
            + self.zwave_host
            + ":"
            + str(self.zwave_port)
            + "/JS/Run/controller.devices.get('"
            + self.zwave_device
            + "').get('metrics:level')"
        )
        logger.info(f"ZwavePlugin: Getting {url} ")

        try:
            resp = requests.get(url, auth=(self.zwave_user, self.zwave_pass))
        except Exception as e:
            logger.error(f"ZwavePlugin: {e}")
            return "unknown"

        if resp.status_code == 200:
            if resp.text == '"off"' or resp.text == '"on"':
                return resp.text.strip('"')

        logger.error(f"ZwavePlugin: {resp.status_code} {resp.text} ")
        return "unknown"
