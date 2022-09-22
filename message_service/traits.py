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

"""A package that provides a higher level interfaces for our application."""

from __future__ import annotations

import typing
import collections.abc as collections

if typing.TYPE_CHECKING:
    from . import enums
    from . import devices


@typing.runtime_checkable
class Runnable(typing.Protocol):
    """An interface for an application than can be ran and shutdown."""

    @property
    def is_alive(self) -> bool:
        """Whether this application is running or not."""
        raise NotImplementedError

    @property
    def endpoint(self) -> str:
        """The base endpoint this object is connected to."""
        raise NotImplementedError

    async def open(self) -> None:
        """Open this application. This will raise a `RuntimeError` if not called within an event loop."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection to this socket.

        Raises a runtime error if its already closed."""
        raise NotImplementedError


@typing.runtime_checkable
class Pull(Runnable, typing.Protocol):
    """A `PULL` socket type protocol. This is considered as the main server that listenes to `PUSH` sockets (Devices)."""

    @property
    def devices(self) -> collections.Mapping[str, devices.DeviceView]:
        """A mapping from each device hostname to a view of that device."""
        raise NotImplementedError

    async def listen(
        self, signal: enums.Signal, callback: collections.Callable[..., typing.Any]
    ) -> None:
        """Listen for a device signal to Occur.

        A callback can be dispatched when this signal is recived.
        """
        raise NotImplementedError


@typing.runtime_checkable
class Push(Runnable, typing.Protocol):
    """A `PUSH` socket type protocol. This is considered as a device that connects to `Pull` object."""

    @property
    def ipv4_address(self) -> str:
        """The IPv4 for this device."""
        raise NotImplementedError

    @property
    def host_name(self) -> str:
        """The hostname for this device."""
        raise NotImplementedError

    @property
    def mac_address(self) -> str:
        """The mac address for this device."""
        raise NotImplementedError

    async def signal(self, signal: enums.Signal) -> None:
        """Send a signal to the gateway for this device."""
        raise NotImplementedError
