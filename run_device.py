import asyncio

from message_service import devices, enums

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def create_many() -> None:
    devs = [devices.Device() for _ in range(10)]
    await asyncio.gather(*(dev.connect() for dev in devs))


if __name__ == "__main__":
    dev = devices.Device()

    async def main():
        await create_many()

    asyncio.run(main())
