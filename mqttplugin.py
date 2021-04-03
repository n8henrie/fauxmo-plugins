"""Fauxmo plugin for simple MQTT requests.

The on and off methods publish a value to the given MQTT queue. The get_status
method subscribes to an MQTT queue to asynchronously receive the status
published from the device. If the device doesn’t publish a status via MQTT then
omit the state_cmd and the plugin will return a status of “unknown”. The status
received from the device is passed back unchanged to fauxmo which is expecting
“on”, “off” or “unknown”.

Behaviour of the plugin is not entirely predictable if mqttserver and mqttport
are omitted, please make sure to set in your config.

Example config:

```
{
    "FAUXMO": {
        "ip_address": "auto"

    },
    "PLUGINS": {
        "MQTTPlugin": {
            "path": "/path/to/mqttplugin.py",
            "DEVICES": [
                {
                    "port": 12349,
                    "on_cmd": [ "Home/Light/Study01", "1" ],
                    "off_cmd": [ "Home/Light/Study01", "0" ],
                    "state_cmd": "Home/Light/Study01",
                    "name":"MQTT Study Light 1",
                    "mqtt_server": "test.mosquitto.org",
                    "mqtt_client_id": "study_light_one",
                    "mqtt_port": 1883
                },
                {
                    "port": 12350,
                    "on_cmd": [ "Home/Light/Study02", "1" ],
                    "off_cmd": [ "Home/Light/Study02", "0" ],
                    "state_cmd": "Home/Light/Study02",
                    "name":"MQTT Study Light 2",
                    "mqtt_server": "test.mosquitto.org",
                    "mqtt_port": 1883
                },
                {
                    "port": 12351,
                    "on_cmd": [
                        "home-assistant/devices/cmnd/sonoff1/POWER",
                        "ON"
                    ],
                    "off_cmd": [
                        "home-assistant/devices/cmnd/sonoff1/POWER",
                        "OFF"
                    ],
                    "state_cmd": "home-assistant/devices/stat/sonoff1/POWER",
                    "name":"Hass MQTT device",
                    "mqtt_server": "192.168.1.108",
                    "mqtt_port": 1883,
                    "mqtt_user": "MyHassUser",
                    "mqtt_pw": "MySecretP@ssword"
                }
            ]
        }
    }
}
```

Dependencies:
    paho-mqtt==1.3.1
"""

from typing import List, Sequence

from fauxmo.plugins import FauxmoPlugin
from paho.mqtt.client import Client, MQTTMessage


class MQTTPlugin(FauxmoPlugin):
    """Fauxmo plugin to interact with an MQTT server by way of paho."""

    def __init__(
        self,
        *,
        name: str,
        port: int,
        off_cmd: Sequence[str],
        on_cmd: Sequence[str],
        mqtt_port: int = 1883,
        mqtt_pw: str = None,
        mqtt_user: str = None,
        mqtt_server: str = "127.0.0.1",
        mqtt_client_id: str = "",
        state_cmd: str = None,
    ) -> None:
        """Initialize an MQTTPlugin instance.

        Kwargs:
            name: device name
            port: Port for Fauxmo to make this device avail to Echo

            mqttport: MQTT server port
            mqttserver: MQTT server address
            mqttclientid: MQTT client id
            mqttuser: MQTT username
            mqttpw: MQTT password
            off_cmd: [ MQTT Queue, value to be publshed as str ] to turn off
            on_cmd: [ MQTT Queue, value to be publshed as str ] to turn on
            state_cmd: MQTT Queue to get state
        """
        self.on_cmd, self.on_value = on_cmd[0], on_cmd[1]
        self.off_cmd, self.off_value = off_cmd[0], off_cmd[1]
        self.state_cmd = state_cmd
        self.status = "unknown"
        self._subscribed = False

        self.client = Client(client_id=mqtt_client_id)
        if mqtt_user or mqtt_pw:
            self.client.username_pw_set(mqtt_user, mqtt_pw)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message

        self.client.connect(mqtt_server, mqtt_port, 60)

        super().__init__(name=name, port=port)

        # Looping thread only seems necessary for status updates
        if self.state_cmd is not None:
            self.client.loop_start()

    @property
    def subscribed(self) -> bool:
        """Property to return whether the subscription has completed."""
        return self._subscribed

    def on_subscribe(
        self, client: Client, userdata: str, mid: int, granted_qos: List[int]
    ) -> None:
        """Set attribute to show that initial subscription is complete."""
        self._subscribed = True

    def on_connect(
        self, client: Client, userdata: str, flags: dict, rc: int
    ) -> None:
        """Subscribe to state command on connect (or reconnect)."""
        if self.state_cmd is not None:
            self.client.subscribe(self.state_cmd)

    def on_message(
        self, client: Client, userdata: str, message: MQTTMessage
    ) -> None:
        """Process an incoming message."""
        status = message.payload.decode("utf-8")

        if status == self.off_value:
            self.status = "off"
        elif status == self.on_value:
            self.status = "on"

    def _publish(self, topic: str, value: str) -> bool:
        msg = self.client.publish(topic, value)
        try:
            msg.wait_for_publish()
        except ValueError:
            return False
        return True

    def on(self) -> bool:
        """Turn on MQTT device.

        Returns:
            True if device seems to have been turned on.

        """
        return self._publish(self.on_cmd, self.on_value)

    def off(self) -> bool:
        """Turn off MQTT device.

        Returns:
            True if device seems to have been turned off.

        """
        return self._publish(self.off_cmd, self.off_value)

    def get_state(self) -> str:
        """Return the self.status attribute.

        `self.status` is set asynchronously in on_message, so it may not
        immediately reflect state changed.

        Returns:
            State if known, else "unknown".

        """
        if self.state_cmd is None:
            return "unknown"

        return self.status
