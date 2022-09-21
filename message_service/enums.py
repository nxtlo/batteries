import enum

__all__ = ("Signal",)


class Signal(int, enum.Enum):
    BEGIN = -1
    CLOSE = 0
    HELLO = 1
    OPEN = 2
    RESTART = 3
    RECONNECT = 4
    DHCP_IP = 5
    RECONNECT_NETWORK_INTERFACE = 6
