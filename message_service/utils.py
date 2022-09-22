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
