from __future__ import annotations

import asyncio
import contextlib
import typing

import connector
import enums
import utils
import logging

try:
    import orjson
    def _dumps(obj: typing.Any) -> str:
        return orjson.dumps(obj).decode("utf-8")

except ImportError:
    import json

    def _dumps(obj: typing.Any) -> str:
        return json.dumps(obj)

if typing.TYPE_CHECKING:
    import aiohttp

class HuaweiVM:
    """Represents a single gateway connection huawei virtual machine."""

    __slots__ = (
        "_transport",
        "_run_task",
        "_ip",
        "_mac",
        "_hostname",
        "_is_dhcp",
        "_logger",
        "_vlan"
    )

    def __init__(
        self,
        ip: str = "",
        mac: str = "",
        hostname: str = "",
        is_dhcp: bool = False,
        vlan: int = 0
    ) -> None:

        # We generate these to ensure nothing is left empty.
        self._hostname = hostname or utils.generate_random_hostname()
        self._ip = ip or utils.generate_random_ipv4_address()   
        self._mac = mac or utils.generate_random_mac_address()

        self._is_dhcp: bool = is_dhcp
        self._run_task: asyncio.Task | None = None
        self._logger: logging.Logger = logging.getLogger("devices")
        self._transport: aiohttp.ClientWebSocketResponse | None = None
        self._vlan: int = vlan

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def is_dhcp(self) -> bool:
        return self._is_dhcp

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def hostname(self) -> str:
        return self._hostname

    def _get_ws(self) -> aiohttp.ClientWebSocketResponse:
        if self._transport is None:
            raise RuntimeError("Websocket not connected...")

        return self._transport

    async def open(self) -> None:
        """Open the connection to the gateway for this device."""

        if self._run_task is not None:
            raise RuntimeError("Already running...")

        run_task = asyncio.create_task(self._run_once())
        self._run_task = run_task
        await asyncio.wait((run_task,), return_when=asyncio.FIRST_COMPLETED)

    async def close(self) -> None:
        """Close the connection to the gateway for this device."""
        if not self._transport:
            return

        await self._send_signal(enums.Signal.CLOSE)

    async def _run_once(self) -> None:
        stack = contextlib.AsyncExitStack()
        gateway = connector.GatewayTransport()

        self._transport = await stack.enter_async_context(gateway.connect())

        await self._send_signal(enums.Signal.OPEN)

        # if opened:
            # await self._send_hello()

    async def _send_hello(self) -> None:
        await self._send_json(
            {
                "device": self.serialize(),
                "signal": "hello",
                "vlan": self._vlan,
            },
        )

    async def _send_str(self, data: str) -> None:
        """Send a string to the gateway for this device."""
        self._logger.info("Sending: %s", data)

        await self._get_ws().send_str(data)

    async def _send_json(self, data: dict[str, typing.Any]) -> None:
        """Send a json object to the gateway."""
        self._logger.info("Sending: %s", data)

        await self._get_ws().send_json(data, dumps=_dumps)

    async def _send_signal(self, signal: enums.Signal) -> bool:
        """Send a signal to the gateway for this device."""

        self._logger.info("Sending signal: %s for device: %s", signal, self)

        match signal:
            case enums.Signal.CLOSE:
                await self._send_json(
                    {"device": self.serialize(), "signal": enums.Signal.CLOSE.name},
                )
                return True
            case enums.Signal.OPEN:
                await self._send_json(
                    {"device": self.serialize(), "signal": enums.Signal.OPEN.name},
                )
                return True
            case enums.Signal.RESTART:
                await self._send_json(
                    {"device": self.serialize(), "signal": enums.Signal.RESTART.name},
                )
                return True
            case enums.Signal.RECONNECT:
                await self._send_json(
                    {"device": self.serialize(), "signal": enums.Signal.RECONNECT.name},
                )
                return True
            case enums.Signal.DHCP_IP:
                await self._send_json(
                    {"device": self.serialize(), "signal": enums.Signal.DHCP_IP.name},
                )
                return True
            case enums.Signal.RECONNECT_NETWORK_INTERFACE:
                await self._send_json(
                    {
                        "device": self.serialize(),
                        "signal": enums.Signal.RECONNECT_NETWORK_INTERFACE.name,
                    },
                )
                return True
            case _:
                return False

    def serialize(self) -> dict[str, int | bool | str]:
        return {
            "ip": self._ip,
            "is_dhcp": self._is_dhcp,
            "mac": self._mac,
            "vlan": self._vlan,
            "hostname": self._hostname,
        }


    def __repr__(self) -> str:
        return f"{type(self).__name__}(ip={self._ip}, mac={self._mac}, hostname={self._hostname})"

    def __str__(self) -> str:
        return f"{self._ip} ({self._mac})"


def create_devices(limit: int = 10, /) -> list[HuaweiVM]:
    return [HuaweiVM() for _ in range(limit)]

def main() -> None:
    async def open_devices() -> None:
        devices = create_devices(10)
        await asyncio.gather(*(dev.open() for dev in devices))

    asyncio.run(open_devices())

if __name__ == '__main__':
    main()