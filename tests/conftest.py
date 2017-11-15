"""conftest.py :: Setup fixtures for pytest."""

import time
from multiprocessing import Process
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

    def __enter__(self) -> str:
        """Start a TextFauxmoServer, returns the ip address it's running on."""
        self.server = Process(target=fauxmo.main,
                              kwargs={'config_path_str': self.config_path_str},
                              daemon=True)
        self.server.start()
        time.sleep(1)
        return get_local_ip()

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value:
                 Optional[Exception], traceback: Optional[TracebackType]) \
            -> None:
        """Terminate the server and join the thread on exit."""
        self.server.terminate()
        self.server.join()


@pytest.fixture(scope="module")
def fauxmo_server() -> Callable[[str], TestFauxmoServer]:
    """Use a pytest fixture to provide the TestFauxmoServer context manager."""
    return TestFauxmoServer
