import asyncio

from message_service import connector, enums

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == '__main__':
    gateway = connector.Gateway()

    with gateway:
        # Listen to when devices open / connect.
        asyncio.run(gateway.listen(enums.Signal.OPEN, callback=lambda: print("Device Opened!")))
