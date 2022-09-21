from __future__ import annotations

__all__ = ("Gateway",)

import logging

import zmq
import zmq.asyncio

from . import devices, enums

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger("connector")


class Gateway:
    __slots__ = ("_context", "_connection", "_devices", "_address", "_count")

    def __init__(self, address: str | None = None) -> None:
        self._context = zmq.asyncio.Context()
        self._connection: zmq.asyncio.Socket | None = None
        self._devices: dict[str, devices.DeviceView] = {}
        self._address = address
        self._count: int = 0

    def open(self) -> None:
        """Open and bind the gateway connection."""
        if self._connection is not None:
            raise RuntimeError("Sockset is already running.")

        self._connection = conn = self._context.socket(zmq.PULL)
        conn.bind(self._address or "tcp://*:5555")
        _LOGGER.info("Connected to gateway...")

    def close(self) -> None:
        if not self._connection:
            raise RuntimeError("Socket is already closed.")

        self._connection.close()

    def _get_connection(self) -> zmq.asyncio.Socket:
        if self._connection:
            return self._connection

        raise RuntimeError("Socket closed...")

    async def listen(self) -> None:
        socket = self._get_connection()

        while True:
            buffer = await socket.recv_multipart()
            dev = devices.deserialize_device(buffer)

            _LOGGER.debug(
                "Device IP: %s Name: %s Event: %s",
                dev.ip_address,
                dev.host_name,
                str(dev.signal),
            )

            match dev.signal:
                case enums.Signal.OPEN if dev not in self._devices:
                    self._devices[dev.host_name] = dev
                case enums.Signal.CLOSE:
                    del self._devices[dev.host_name]
                case enums.Signal.RESTART:
                    # Access device hardware or API to restart?
                    _LOGGER.info("Restarting device %s", dev.host_name)
                case enums.Signal.HELLO:
                    _LOGGER.info("Device %s sent signal HELLO", dev.host_name)
                case _:
                    return

    def __enter__(self) -> Gateway:
        self.open()
        return self

    def __exit__(self, _, __, ___) -> None:
        self._get_connection().close()
