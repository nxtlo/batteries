import asyncio

from message_service import connector, enums

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    gateway = connector.Gateway()

    with gateway:
        asyncio.run(gateway.listen())
