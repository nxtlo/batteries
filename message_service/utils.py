__all__ = (
    "all_of",
    "generate_random_ipv4_address",
    "generate_random_mac_address",
    "generate_random_hostname",
    "get_or_make_loop",
)

import asyncio
import typing

import faker
import faker.providers.internet as internet

T_co = typing.TypeVar("T_co", covariant=True)


def get_or_make_loop() -> asyncio.AbstractEventLoop:
    """Get the current usable event loop or create a new one.
    Returns
    -------
    asyncio.AbstractEventLoop
    """
    # get_event_loop will error under oddly specific cases such as if set_event_loop has been called before even
    # if it was just called with None or if it's called on a thread which isn't the main Thread.
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()

        # Closed loops cannot be re-used.
        if not loop.is_closed():
            return loop

    except RuntimeError:
        pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


async def all_of(
    *aws: typing.Awaitable[T_co],
    timeout: typing.Optional[float] = None,
) -> typing.Sequence[T_co]:
    fs = list(map(asyncio.ensure_future, aws))
    gatherer = asyncio.gather(*fs)

    try:
        return await asyncio.wait_for(gatherer, timeout=timeout)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("all_of gatherer timed out") from None
    except asyncio.CancelledError:
        raise asyncio.CancelledError("all_of gatherer cancelled") from None
    finally:
        for f in fs:
            if not f.done() and not f.cancelled():
                f.cancel()
                # Asyncio gathering futures complain if not awaited after cancellation
                try:
                    await f
                except asyncio.CancelledError:
                    pass

        gatherer.cancel()
        try:
            # coverage.py will complain that this is not fully covered, as the
            # "except" block will always be hit. This is intentional.
            await gatherer  # pragma: no cover
        except asyncio.CancelledError:
            pass


_fake = faker.Faker()
_fake.add_provider(internet)


def generate_random_ipv4_address() -> str:
    """Generate a random IPv4 address."""
    return _fake.ipv4_private()


def generate_random_mac_address() -> str:
    """Generate a random MAC address."""
    return _fake.mac_address()


def generate_random_hostname() -> str:
    """Generate a random hostname."""
    return _fake.hostname(0)
