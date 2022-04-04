from __future__ import annotations

import asyncio
import collections.abc as collections
import contextlib
import logging

import aiohttp

logging.basicConfig(level=logging.DEBUG)

class GatewayTransport:
    """Represents a websocket connection to the gateway."""

    __slots__ = ("_host", "_port", "_client_session", "_logger")

    def __init__(self, host: str = "localhost", port: str = "8000") -> None:
        self._host = host
        self._port = port
        self._client_session: aiohttp.ClientSession | None = None
        self._logger = logging.getLogger("connector")

    def _get_session(self) -> aiohttp.ClientSession:
        if self._client_session is None:
            self._client_session = aiohttp.ClientSession()

        return self._client_session

    @contextlib.asynccontextmanager
    async def connect(self) -> collections.AsyncGenerator[aiohttp.ClientWebSocketResponse, None]:
        session = self._get_session()
        stack = contextlib.AsyncExitStack()

        self._logger.debug("Connecting to %s:%s", self._host, self._port)

        try:
            ws = await stack.enter_async_context(
                session.ws_connect(
                    f"http://{self._host}:{self._port}/ws/",
                    autoclose=False,
                    autoping=False,
                    max_msg_size=0,
                )
            )

            try:
                yield ws

            except Exception:
                self._logger.exception(
                    "Encountered an error while yielding the websocket.", exc_info=True
                )
                raise

            finally:
                await ws.close()

        except (
            aiohttp.ClientError,
            aiohttp.ClientConnectionError,
            aiohttp.WSServerHandshakeError,
            aiohttp.ServerDisconnectedError,
        ) as e:
            self._logger.error("Connection error: %s", e)
            raise

        finally:
            await stack.aclose()
            await session.close()
            await asyncio.sleep(0.25)
