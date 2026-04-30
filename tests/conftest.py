import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_optional_dependency_stubs():
    if "psutil" not in sys.modules:
        psutil = types.ModuleType("psutil")
        psutil.net_if_addrs = lambda: {}
        sys.modules["psutil"] = psutil

    if "ping3" not in sys.modules:
        ping3 = types.ModuleType("ping3")
        ping3.ping = lambda *_args, **_kwargs: None
        sys.modules["ping3"] = ping3

    if "requests" not in sys.modules:
        requests = types.ModuleType("requests")

        class RequestException(Exception):
            pass

        class Session:
            def get(self, *_args, **_kwargs):
                raise RequestException("requests is not installed in this test environment")

        requests.RequestException = RequestException
        requests.Session = Session
        sys.modules["requests"] = requests


_install_optional_dependency_stubs()
