import asyncio

from message_service import devices, enums

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == '__main__':
    dev = devices.Device()

    async def main():
        async with dev:
            await dev.send_signal(enums.Signal.OPEN)

    asyncio.run(main())
