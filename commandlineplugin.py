"""restapiplugin.py

Runs a `shlex`ed command using `subprocess.run`, keeping the default of
`shell=False`. This is probaby frought with security concerns, which is why
this plugin is not included by default in `fauxmo.plugins`. By installing or
using it, you acknowledge that it could run commands from your config.json that
could lead to data compromise, corruption, loss, etc. Consider making your
config.json read-only. If there are parts of this you don't understand, you
should probably not use this plugin.

If the command runs with a return code of 0, Alexa should respond prompty
"Okay" or something that indicates it seems to have worked. If the command has
a return code of anything other than 0, Alexa stalls for several seconds and
subsequently reports that there was a problem (which should notify the user
that something didn't go as planned).

Note that `subprocess.run` as implemented in this plugin doesn't handle complex
commands with pipes, redirection, or multiple statements joined by `&&`, `||`,
`;`, etc., so you can't just use e.g. `"command that sometimes fails || true"`
to avoid the delay and Alexa's response. If you really want to handle more
complex commands, consider using this plugin as a template for another one
using `os.system` instead of `subprocess.run`, but realize that this comes with
substantial security risks that exceed my ability to explain.

Example config:
```
{
  "FAUXMO": {
    "ip_address": "auto"
  },
  "PLUGINS": {
    "CommandLinePlugin": {
      "DEVICES": [
        {
            "name": "output stuff to a file",
            "port": 49915,
            "on_cmd": "touch testfile.txt",
            "off_cmd": "rm testfile.txt"
        }
      ]
    }
  }
}
```
"""

from functools import partialmethod  # type: ignore
import shlex
import subprocess

from fauxmo.plugins import FauxmoPlugin


class CommandLinePlugin(FauxmoPlugin):
    """Fauxmo Plugin for running commands on the local machine."""

    def __init__(self, name: str, port: int, on_cmd: str, off_cmd: str) \
            -> None:
        """Initialize a CommandLinePlugin instance.

        Args:
            name: Name for this Fauxmo device
            port: Port on which to run a specific CommandLinePlugin instance
            on_cmd: Command to be called when turning device on
            off_cmd: Command to be called when turning device off
       """

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

        super().__init__(name=name, port=port)

    def run_cmd(self, cmd: str) -> bool:
        """Partialmethod to run command.

        Args:
            cmd: Will be one of `"on_cmd"` or `"off_cmd"`, which `getattr` will
                 use to get the instance attribute.
        """

        command_str = getattr(self, cmd)
        shlexed_cmd = shlex.split(command_str)
        process = subprocess.run(shlexed_cmd)
        return process.returncode == 0

    on = partialmethod(run_cmd, "on_cmd")
    off = partialmethod(run_cmd, "off_cmd")
