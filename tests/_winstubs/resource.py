"""Windows-only stand-in for the POSIX ``resource`` module.

``homeassistant.util.resource`` unconditionally imports ``resource`` to
adjust the open file descriptor limit, which is only ever called from
``homeassistant.runner`` (never exercised by this test suite). See
``fcntl.py`` in this same directory for why the stub has to live on
``pythonpath`` rather than in a conftest.py. On real POSIX systems this
file steps aside so the genuine standard-library extension module is used
instead.
"""

from __future__ import annotations

import os
import sys

if sys.platform == "win32":
    RLIMIT_NOFILE = 7

    def getrlimit(resource_id: int) -> tuple[int, int]:
        """No-op stand-in; never exercised by the test suite."""

        return (0, 0)

    def setrlimit(resource_id: int, limits: tuple[int, int]) -> None:
        """No-op stand-in; never exercised by the test suite."""
else:
    import importlib.machinery
    import importlib.util

    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _search_path = [
        path for path in sys.path if os.path.abspath(path or os.curdir) != _this_dir
    ]

    _spec = importlib.machinery.PathFinder.find_spec("resource", _search_path)

    if _spec is None or _spec.loader is None:
        raise ModuleNotFoundError("No module named 'resource'")

    _real_resource = importlib.util.module_from_spec(_spec)
    sys.modules[__name__] = _real_resource
    _spec.loader.exec_module(_real_resource)
