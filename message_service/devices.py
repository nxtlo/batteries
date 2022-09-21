from __future__ import annotations

import asyncio

__all__ = ("Device", "deserialize_device")

import asyncio
import dataclasses
import json
import logging
import typing

import zmq
import zmq.asyncio

from . import enums, utils

_LOGGER = logging.getLogger("devices")


@dataclasses.dataclass(slots=True, unsafe_hash=True)
class DeviceView:
    host_name: str
    ip_address: str
    mac_address: str
    signal: enums.Signal | None


# TODO: Create an async trait for PUSH / PULL socket types.


class Device:
    __slots__ = (
        "_context",
        "_socket",
        "_endpoint",
        "_host_name",
        "_ip_address",
        "_mac_address",
    )

    def __init__(
        self,
        host_name: str | None = None,
        ip_address: str | None = None,
        mac_address: str | None = None,
        endpoint: str | None = None,
    ) -> None:

        # Connection information.
        self._context = zmq.asyncio.Context()
        self._socket: zmq.asyncio.Socket | None = None
        self._endpoint = endpoint

        # Device information
        self._host_name = host_name or utils.generate_random_hostname()
        self._ip_address = ip_address or utils.generate_random_ipv4_address()
        self._mac_address = mac_address or utils.generate_random_mac_address()

    @property
    def endpoint(self) -> str:
        return self._endpoint if self._endpoint else "tcp://127.0.0.1:5555"

    @property
    def ipv4_address(self) -> str:
        return self._ip_address

    @property
    def host_name(self) -> str:
        return self._host_name

    @property
    def mac_address(self) -> str:
        return self._mac_address

    async def connect(self) -> None:
        """Connect to the gateway."""
        if self._socket is not None:
            raise RuntimeError("Sockset is already running.")

        loop = utils.get_or_make_loop()
        self._socket = sock = self._context.socket(zmq.PUSH)
        _LOGGER.info("Connecting to server...")

        await loop.run_in_executor(
            None, sock.connect, self._endpoint or "tcp://localhost:5555"
        )

        if await self._send_signal(enums.Signal.HELLO):
            await self._send_signal(enums.Signal.OPEN)
            _LOGGER.info("Connected to server...")

    async def close(self) -> None:
        """Close the connection for this device."""
        if not self._socket:
            raise RuntimeError("Socket is already closed.")

        loop = asyncio.get_running_loop()
        await self._send_signal(enums.Signal.CLOSE)
        await loop.run_in_executor(None, self._socket.close)

    def box(self) -> dict[str, typing.Any]:
        """Box this device into a Python dict serializing it."""
        return {
            "ip_address": self._ip_address,
            "mac_address": self._mac_address,
            "host_name": self._host_name,
        }

    def unbox(self, payload: typing.Optional[dict[str, typing.Any]] = None) -> bytes:
        """Unbox this device into bytes to be sent to the gateway.

        Parameters
        ----------
        payload: dict[str, Any] | None
            If provided, The payload will be sent instead of `Self`.
            This parameter is usually used to insert extra data to the payload.
        """
        return json.dumps(payload if payload else self.box()).encode("UTF-8")

    async def _send_signal(
        self, signal: enums.Signal
    ) -> typing.Optional[zmq.MessageTracker]:
        """Send a signal to the server for this device."""
        device = self.box()
        device["signal"] = signal

        socket = self._get_socket()
        await socket.send_multipart([self.unbox(device)])

    def _get_socket(self) -> zmq.asyncio.Socket:
        if self._socket:
            return self._socket

        raise RuntimeError("Socket closed...")


def deserialize_device(data: list[bytes]) -> DeviceView:
    payload: dict[str, typing.Any] = json.loads(data[0])
    return DeviceView(
        host_name=payload["host_name"],
        ip_address=payload["ip_address"],
        mac_address=payload["mac_address"],
        signal=enums.Signal(payload["signal"]) if "signal" in payload else None,
    )
