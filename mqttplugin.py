""" Fauxmo plugin for simple MQTT requests. Requires paho-mqtt v1.3.1 (https://www.eclipse.org/paho/clients/python/docs/)

The on and off methods publish a value to the given MQTT queue. The get_status method 
subscribes to an MQTT queue to asynchronously receive the status published from the device. 
If the device doesn’t publish a status via MQTT then omit the state_cmd and the plugin will 
return a status of “unknown”. The status received from the device is passed back unchanged
to fauxmo which is expecting “on”, “off” or “unknown”.

It is expected that MQTTserver and MQTTport are set at the plugin level (example below).
Whilst checks are performed to ensure the existence of these variables the behaviour of
the plugin is not entirely predictable if they are omitted.

Sample json.config:

{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "MQTTPlugin": {
            "MQTTserver":"10.0.4.5",
            "MQTTport":1883,
            "DEVICES": [
                {
                    "port":12349,
                    "on_cmd":["Home/Light/Study01",1],
                    "off_cmd":["Home/Light/Study01",0],
                    "state_cmd":["Home/Light/Study01/Stat"],
                    "name":"Study Light"
                }
            ]
        }
    }
}

The on and off commands are an array of two elements where the first is the queue and the second 
is the value to be published to the queue. The state command only requires the queue to which
the status is published and this plugin subscribes. 

Perforex Jan 2018
"""

import paho.mqtt.client as mqtt
import logging
from fauxmo.plugins import FauxmoPlugin
from fauxmo import __version__, logger

class MQTTPlugin(FauxmoPlugin):

    def __init__(
            self,
            *,
            name: str,
            off_cmd: str,
            on_cmd: str,
            state_cmd: str = None,
            port:int,
            MQTTserver: str = None,
            MQTTport: int = None,
            ) -> None:

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.state_cmd = state_cmd
        self.qserver = MQTTserver
        self.qport = MQTTport
        self.status = "unknown"
        self.client = mqtt.Client()
        super().__init__(name=name,port=port)
		
        self.client.connect(self.qserver,self.qport,60)
        self.client.on_message = self.on_message
        self.client.subscribe(self.state_cmd[0])
        self.client.loop_start() 
		
        if not self.check_mqtt(): return False

    def on_message(self,client, userdata, msg):
        self.status=msg.payload.decode('utf-8')

    def on(self) -> bool:

        self.client.publish(self.on_cmd[0],self.on_cmd[1]);

        return True

    def off(self) -> bool:

        self.client.publish(self.off_cmd[0],self.off_cmd[1]);

        return True

    def get_state(self) -> str:
        print( "MQTT: Get State")

        if(self.state_cmd is None): return "unknown"

        self.client.on_message = self.on_message
        self.client.subscribe(self.state_cmd[0])

        return self.status

    def check_mqtt(self) -> bool:

        logger = logging.getLogger("fauxmo")
        if(self.qserver is None): 
            logger.error("MQTTserver not provided in config.json.\n")
            return False    

        if(self.qport is None): 
            logger.error("MQTTport not provided in config.json.\n")
            return False
			
        return True                   