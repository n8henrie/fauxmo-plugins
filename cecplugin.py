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

from fauxmo.plugins import FauxmoPlugin
import cec

class CECPlugin(FauxmoPlugin):
    """Fauxmo plugin to interact with devices over HDMI-CEC via an adapter.
    
    Often, the default Kwargs are enough to get things working.
    If you're having issues getting the TV to detect, you should try setting fake_state to True in the config.
    """


    def __init__(
        self,
        *,
        name: str,
        port: int,
        cec_adapter: str = None,
        tv_address: str = "0.0.0.0",
        fake_state: bool = False
    ) -> None:
        """Initialize a CECPlugin instance.

        Kwargs:
            name: Device name
            port: Port for Fauxmo to make this device avail to Echo
            cec_adapter: A full path to the adapter port (Optional, defaults to first adapter detected by libcec)
            cec_address: The cec device address to control (Optional, defaults to 0.0.0.0 aka address 0)
            fake_state: Whether or not the cec device should be queried for state or not (Optional, defaults to False)
        """

        self.cec_adapter = cec_adapter
        self.tv_address = tv_address
        self.fake_state = fake_state

        # Init CEC connection
        if self.cec_adapter:
            cec.init(cec_adapter)
        else:
            cec.init()

        self.tv_address = int(self.tv_address.split('.', 1)[0])
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
        """Get power status for the device
        Returns:
            "on" or "off"
            If fake_state is set to True, it does not query the cec device for it's status.
        """
        if (self.fake_state):
            return super().get_state()
        else:
            return "on" if self.device.is_on() else "off"
