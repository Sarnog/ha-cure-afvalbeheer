"""Windows-only stand-in for the POSIX ``fcntl`` module.

``homeassistant.runner`` unconditionally imports ``fcntl`` for a
single-instance pidfile lock. ``pytest-homeassistant-custom-component``
pulls that module in as soon as it is loaded, which happens before pytest
has read any conftest.py (plugin autoloading runs before conftest
collection), so the stub has to be reachable via ``pythonpath`` instead.
The lock itself is never exercised by this test suite. On real POSIX
systems this file steps aside so the genuine standard-library extension
module is used instead.
"""

from __future__ import annotations

import contextlib
import os
import sys

if sys.platform == "win32":
    import socket as _socket_module

    def flock(fd: int, operation: int) -> None:
        """No-op stand-in; the pidfile lock is never exercised in tests."""

    LOCK_EX = 2
    LOCK_NB = 4
    LOCK_UN = 8

    # Every asyncio event loop on Windows needs a socket.socketpair() self
    # pipe (there is no native socketpair syscall, so CPython emulates it
    # with a connected loopback TCP pair). pytest-homeassistant-custom
    # -component's session-scoped autouse fixtures need an event loop before
    # any test runs, but pytest_socket later replaces socket.socket with a
    # guard that blocks exactly this loopback pair. Capture the real socket
    # class now, before pytest_socket ever patches it, and rebuild the
    # fallback pair implementation around that saved reference so the
    # self-pipe keeps working while other code still gets blocked.
    _real_socket_cls = _socket_module.socket

    def _unblocked_fallback_socketpair(family=None, type=None, proto=0):
        family = family if family is not None else _socket_module.AF_INET
        type = type if type is not None else _socket_module.SOCK_STREAM

        lsock = _real_socket_cls(family, type, proto)
        try:
            lsock.bind(("127.0.0.1", 0))
            lsock.listen()
            addr, port = lsock.getsockname()[:2]
            csock = _real_socket_cls(family, type, proto)
            try:
                csock.setblocking(False)
                with contextlib.suppress(BlockingIOError, InterruptedError):
                    csock.connect((addr, port))
                csock.setblocking(True)
                # lsock.accept() would construct the accepted connection via
                # the module-level "socket" name inside the stdlib socket
                # module, which is exactly the name pytest_socket replaces.
                # Do the low-level accept ourselves and wrap the resulting
                # fd with the saved real class instead.
                fd, _ = lsock._accept()
                ssock = _real_socket_cls(family, type, proto, fileno=fd)
            except BaseException:
                csock.close()
                raise
        finally:
            lsock.close()

        return (ssock, csock)

    _socket_module.socketpair = _unblocked_fallback_socketpair
    _socket_module._fallback_socketpair = _unblocked_fallback_socketpair
else:
    import importlib.machinery
    import importlib.util

    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _search_path = [
        path for path in sys.path if os.path.abspath(path or os.curdir) != _this_dir
    ]

    _spec = importlib.machinery.PathFinder.find_spec("fcntl", _search_path)

    if _spec is None or _spec.loader is None:
        raise ModuleNotFoundError("No module named 'fcntl'")

    _real_fcntl = importlib.util.module_from_spec(_spec)
    sys.modules[__name__] = _real_fcntl
    _spec.loader.exec_module(_real_fcntl)
