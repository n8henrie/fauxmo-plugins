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
                    "initial_state": "on",
                    "use_fake_state": False,
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
    paho-mqtt==2.1.0
"""

import typing as t

from fauxmo.plugins import FauxmoPlugin
from paho.mqtt.client import CallbackAPIVersion, Client, MQTTMessage


class MQTTPlugin(FauxmoPlugin):
    """Fauxmo plugin to interact with an MQTT server by way of paho."""

    def __init__(
        self,
        *,
        name: str,
        port: int,
        initial_state: t.Optional[str] = None,
        off_cmd: t.Sequence[str],
        on_cmd: t.Sequence[str],
        mqtt_port: int = 1883,
        mqtt_pw: t.Optional[str] = None,
        mqtt_user: str = "",
        mqtt_server: str = "127.0.0.1",
        mqtt_client_id: str = "",
        state_cmd: t.Optional[str] = None,
        use_fake_state: bool = False,
    ) -> None:
        """Initialize an MQTTPlugin instance.

        `initial_state` may be required when initially adding a MQTT device to
        Alexa, as the `state_cmd` is called asynchronously instead of on
        demand. This means that when adding a new device, Alexa will likely get
        an `"unknown"` result, which the Fauxmo server will discard as invalid
        and fail to return a successul response to the Echo. Setting an
        arbitrary `initial_state` should allow the device to be added, and
        after the first call to the `on()` or `off()` methods the state should
        be properly updated and reflected on subsequent `get_state()` calls.

        See also: https://github.com/n8henrie/fauxmo-plugins/issues/26

        Kwargs:
            name: device name
            port: Port for Fauxmo to make this device avail to Echo

            mqttport: MQTT server port
            mqttserver: MQTT server address
            mqttclientid: MQTT client id
            mqttuser: MQTT username
            mqttpw: MQTT password
            initial_state: "on"|"off" see explanation above
            off_cmd: [ MQTT Queue, value to be publshed as str ] to turn off
            on_cmd: [ MQTT Queue, value to be publshed as str ] to turn on
            state_cmd: MQTT Queue to get state
            use_fake_state: If `True`, override `get_state` to return the
                            latest action as the device state. NB: The proper
                            json boolean value for Python's `True` is `true`,
                            not `True` or `"true"`.
        """
        self.on_cmd, self.on_value = on_cmd[0], on_cmd[1]
        self.off_cmd, self.off_value = off_cmd[0], off_cmd[1]
        self.state_cmd = state_cmd
        self.status = "unknown"
        self._subscribed = False
        self.initial_state = initial_state
        self.use_fake_state = use_fake_state

        self.client = Client(
            CallbackAPIVersion.VERSION1, client_id=mqtt_client_id
        )
        if mqtt_user or mqtt_pw:
            self.client.username_pw_set(mqtt_user, mqtt_pw)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message

        self.client.connect(mqtt_server, mqtt_port, 60)

        super().__init__(name=name, port=port, initial_state=initial_state)

        self.client.loop_start()

    @property
    def subscribed(self) -> bool:
        """Property to return whether the subscription has completed."""
        return self._subscribed

    def on_subscribe(
        self,
        client: Client,
        userdata: str,
        mid: int,
        granted_qos: t.Tuple[int, ...],
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

    def publish(self, topic: str, value: str) -> bool:
        """Publish `value` to `topic`."""
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
        return self.publish(self.on_cmd, self.on_value)

    def off(self) -> bool:
        """Turn off MQTT device.

        Returns:
            True if device seems to have been turned off.

        """
        return self.publish(self.off_cmd, self.off_value)

    def get_state(self) -> str:
        """Return the self.status attribute.

        `self.status` is set asynchronously in `on_message`, so it may not
        immediately reflect state changed.

        Returns:
            State if known, else "unknown".

        """
        if self.status != "unknown":
            return self.status

        if self.initial_state is not None:
            state, self.initial_state = self.initial_state, None
            return state

        if self.use_fake_state is True:
            return super().get_state()

        return "unknown"
