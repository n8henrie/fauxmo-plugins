"""Fauxmo plugin for controlling HDMI CEC devices like your TV power.

The on and off methods simply call power_on() and power_off() for a configured
CEC address from the specified CEC adapter.

Example config:

```
{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "CECPlugin": {
            "path": "/path/to/cecplugin.py",
            "DEVICES": [
                {
                    "name": "TV",
                    "port": 12349,
                    "cec_adapter": "/dev/ttyACM0"
                }
            ]
        }
    }
}
```

Hardware:
    A compatable HDMI-CEC adapter/injector:
        https://www.pulse-eight.com/p/104/usb-hdmi-cec-adapter
    or just use a Raspberry pi's HDMI port

Package Dependencies:
    libcec
    libcec-dev
    buildessential
    python3-dev

PyPi Dependencies:
    cec>=0.2.8
"""

from __future__ import annotations

import typing as t

import cec
from fauxmo.plugins import FauxmoPlugin


class CECPlugin(FauxmoPlugin):
    """Fauxmo plugin to interact with devices over HDMI-CEC via an adapter.

    Often, the default Kwargs are enough to get things working.
    """

    def __init__(
        self,
        *,
        name: str,
        port: int,
        cec_adapter: t.Optional[str] = None,
        tv_address: str = "0.0.0.0",
    ) -> None:
        """Initialize a CECPlugin instance.

        Kwargs:
            name: Device name
            port: Port for Fauxmo to make this device avail to Echo
            cec_adapter: A full path to the adapter port (Optional, defaults to
                         first adapter detected by libcec)
            cec_address: The cec device address to control (Optional, defaults
                         to 0.0.0.0 aka address 0)
        """
        self.cec_adapter = cec_adapter
        self.tv_address = int(tv_address.split(".", 1)[0])

        # Init CEC connection
        if self.cec_adapter:
            cec.init(cec_adapter)
        else:
            cec.init()

        self.device = cec.Device(self.tv_address)

        super().__init__(name=name, port=port)

    def on(self) -> bool:
        """Turn on CEC device.

        Returns:
            True if device seems to have been turned on.
        """
        return self.device.power_on()

    def off(self) -> bool:
        """Turn off CEC device.

        Returns:
            True if device seems to have been turned off.
        """
        return self.device.standby()

    def get_state(self) -> str:
        """Get power status for the device.

        Returns:
            super().get_state()
        """
        return super().get_state()
