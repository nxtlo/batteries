import logging
import typing

import fastapi
import uvicorn

import utils

app = fastapi.FastAPI(debug=True)
logging.basicConfig(level=logging.DEBUG)

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("shards.sockets")

class WebsocketManager:
    __slots__ = ("_sockets",)

    def __init__(self) -> None:
        self._sockets: set[fastapi.WebSocket] = set()

    @property
    def sockets(self) -> set[fastapi.WebSocket]:
        return self._sockets

    async def open(self, socket: fastapi.WebSocket) -> None:
        await socket.accept()

    async def stop(self, socket: fastapi.WebSocket) -> None:
        _LOGGER.debug("Stopping socket %s", socket)

        if socket in self._sockets:
            self._sockets.remove(socket)

        await socket.close()
        _LOGGER.info("Stopped socket %s", socket)

    async def wait(self, socket: fastapi.WebSocket) -> dict[str, typing.Any]:
        builder: dict[str, typing.Any] = {}

        while True:
            data = await socket.receive_json()
            if data:
                return builder | data

            break

        return builder

    async def send_back(self, socket: fastapi.WebSocket, message: dict[str, typing.Any]) -> None:
        # await socket.send_json(message)
        raise NotImplementedError("Devices can't send back messages currently.")

    async def stop_all(self) -> None:
        await utils.all_of(*(socket.close() for socket in self._sockets))
        self._sockets.clear()

    async def dispatch(self, message: dict[str, typing.Any]) -> None:
        # await utils.all_of(*(socket.send_json(message) for socket in self._sockets))
        raise NotImplementedError("Devices can't send messages currently.")

manager = WebsocketManager()

@app.websocket("/ws/")
async def ws_home(websocket: fastapi.WebSocket) -> None:
    await manager.open(websocket)

    try:
        msg = await manager.wait(websocket)
        print(msg)
    except fastapi.WebSocketDisconnect:
        await manager.stop_all()

def main() -> None:
    uvicorn.run(app)

if __name__ == "__main__":
    main()