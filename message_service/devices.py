# BSD 3-Clause License

# Copyright (c) 2022-Present, nxtlo
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from __future__ import annotations


__all__ = ("Device", "deserialize_device")

import asyncio
import dataclasses
import json
import logging
import typing

import zmq
import zmq.asyncio

from . import enums, utils, traits

_LOGGER = logging.getLogger("devices")


@dataclasses.dataclass(slots=True, unsafe_hash=True)
class DeviceView:
    host_name: str
    ip_address: str
    mac_address: str
    signal: enums.Signal


# TODO: Create an async trait for PUSH / PULL socket types.


class Device(traits.Push):
    __slots__ = (
        "_context",
        "_socket",
        "_endpoint",
        "_host_name",
        "_ip_address",
        "_connected_event",
        "_lock" "_mac_address",
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

        # Asyncio stuff.
        self._connected_event = asyncio.Event()
        self._lock = asyncio.Lock()

        # Device information
        self._host_name = host_name or utils.generate_random_hostname()
        self._ip_address = ip_address or utils.generate_random_ipv4_address()
        self._mac_address = mac_address or utils.generate_random_mac_address()

    @property
    def endpoint(self) -> str:
        return self._endpoint if self._endpoint else "tcp://127.0.0.1:5555"

    @property
    def is_alive(self) -> bool:
        return self._socket is not None

    @property
    def ipv4_address(self) -> str:
        return self._ip_address

    @property
    def host_name(self) -> str:
        return self._host_name

    @property
    def mac_address(self) -> str:
        return self._mac_address

    async def open(self) -> None:
        self._connected_event.clear()

        if self._socket is not None:
            raise RuntimeError("This device is already running.")

        _LOGGER.info("Connecting to gateway...")
        self._socket = self._context.socket(zmq.PUSH)
        self._socket.connect(self._endpoint or "tcp://localhost:5555")
        _LOGGER.info("Connection opened to gateway...")
        self._connected_event.set()

    async def close(self) -> None:
        """Close the connection for this device."""
        if not self._socket:
            raise RuntimeError("Socket is already closed.")

        await self.signal(enums.Signal.CLOSE)
        self._socket.close()
        self._socket = None

    async def signal(self, signal: enums.Signal) -> None:
        """Send a signal to the server for this device."""
        async with self._lock:
            try:
                await self._get_socket().send_multipart([self._unbox(signal)], copy=False)
            except zmq.ZMQError as e:
                _LOGGER.info(
                    "An error occured while trying to send a signal for device %s. ERRNO: %s",
                    self.host_name,
                    e.errno,
                )
                raise

    def _box(self) -> dict[str, typing.Any]:
        """Box this device into a Python dict serializing it."""
        return {
            "ip_address": self._ip_address,
            "mac_address": self._mac_address,
            "host_name": self._host_name,
        }

    def _unbox(self, signal: enums.Signal) -> bytes:
        """Unbox this device into bytes to be sent to the gateway.

        Parameters
        ----------
        payload: dict[str, Any] | None
            If provided, The payload will be sent instead of `Self`.
            This parameter is usually used to insert extra data to the payload.
        """
        dev = self._box()
        dev['signal'] = signal
        return json.dumps(dev).encode("UTF-8")

    def _get_socket(self) -> zmq.asyncio.Socket:
        if self._socket:
            return self._socket

        raise RuntimeError("Socket closed...")

def deserialize_device(data: list[zmq.Frame]) -> DeviceView:
    device: dict[str, typing.Any] = json.loads(data[0].bytes)
    return DeviceView(
        host_name=device["host_name"],
        ip_address=device["ip_address"],
        mac_address=device["mac_address"],
        signal=enums.Signal(device['signal']),
    )
