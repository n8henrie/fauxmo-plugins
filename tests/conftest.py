"""conftest.py :: Setup fixtures for pytest."""

import json
import multiprocessing as mp
import socket
import time
from types import TracebackType
from typing import Callable, Optional, Type

import pytest
from fauxmo import fauxmo
from fauxmo.utils import get_local_ip


class TestFauxmoServer:
    """Runs Fauxmo in a separate thread."""

    def __init__(self, config_path_str: str) -> None:
        """Initialize test Fauxmo server with path to config."""
        self.config_path_str = config_path_str
        with open(config_path_str) as f:
            config = json.load(f)
        first_plugin = [*config["PLUGINS"].values()][0]
        self.first_port = first_plugin["DEVICES"][0]["port"]

    def __enter__(self) -> str:
        """Start a TextFauxmoServer, returns the ip address it's running on."""
        ctx = mp.get_context('fork')
        self.server = ctx.Process(
            target=fauxmo.main,
            kwargs={"config_path_str": self.config_path_str},
            daemon=True,
        )
        self.server.start()

        local_ip = get_local_ip()
        for _retry in range(10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((local_ip, self.first_port))
            except ConnectionRefusedError:
                time.sleep(0.1)
                continue
            break

        return local_ip

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[Exception],
        traceback: Optional[TracebackType],
    ) -> None:
        """Terminate the server and join the thread on exit."""
        self.server.terminate()
        self.server.join()


@pytest.fixture(scope="module")
def fauxmo_server() -> Callable[[str], TestFauxmoServer]:
    """Use a pytest fixture to provide the TestFauxmoServer context manager."""
    return TestFauxmoServer
