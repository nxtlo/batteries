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


__all__ = ("Gateway",)

import logging
import asyncio
import typing
import functools

import zmq
import zmq.asyncio

from . import devices, enums, traits

if typing.TYPE_CHECKING:
    import collections.abc as collections

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger("connector")


class Gateway(traits.Pull):
    __slots__ = ("_context", "_socket", "_devices", "_address", "_lock")

    def __init__(self, address: str | None = None) -> None:
        self._context = zmq.asyncio.Context()
        self._socket: zmq.asyncio.Socket | None = None
        self._devices: dict[str, devices.DeviceView] = {}
        self._address = address or "tcp://127.0.0.1:5555"
        self._lock = asyncio.Lock()

    @property
    def is_alive(self) -> bool:
        return self._socket is not None

    @property
    def endpoint(self) -> str:
        return self._address

    @property
    def devices(self) -> collections.Mapping[str, devices.DeviceView]:
        return self._devices

    async def open(self) -> None:
        if self._socket is not None:
            raise RuntimeError("Sockset is already running.")

        self._socket = self._context.socket(zmq.PULL)

        self._socket.set_hwm(1)
        self._socket.bind(self._address)

        _LOGGER.info("Connected to gateway...")
        await self._run_once()

    async def close(self) -> None:
        if not self._socket:
            raise RuntimeError("Socket is already closed.")

        self._socket.close()

    def _dispatch(self, data: list[zmq.Frame], signal: enums.Signal | None = None) -> None:
        dev = devices.deserialize_device(data)
        _LOGGER.debug(
            "Device IP: %s Name: %s Event: %s",
            dev.ip_address,
            dev.host_name,
            dev.signal.name,
        )

        sig = signal or dev.signal
        match sig:
            case enums.Signal.OPEN if dev not in self._devices:
                self._devices[dev.host_name] = dev
                _LOGGER.info("%s", self._devices)
            case enums.Signal.CLOSE:
                del self._devices[dev.host_name]
            case enums.Signal.RESTART:
                # Access device hardware or API to restart?
                _LOGGER.info("Restarting device %s", dev.host_name)
            case enums.Signal.HELLO:
                _LOGGER.info("Device %s sent signal HELLO", dev.host_name)
            case _:
                return

    def _get_socket(self) -> zmq.asyncio.Socket:
        if self._socket:
            return self._socket

        raise RuntimeError("Socket is closed...")

    async def _run_once(self, signal: enums.Signal | None = None) -> None:
        socket = self._get_socket()
        async with self._lock:
            while True:
                try:
                    # {'ip_address': '...', 'signal': '...'}
                    buffer = await socket.recv_multipart(copy=False)
                except zmq.ZMQError:
                    _LOGGER.error("Error occurred while trying to recive data.")
                    raise

                self._dispatch(buffer, signal)
