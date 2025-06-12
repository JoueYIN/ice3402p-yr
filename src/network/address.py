from dataclasses import dataclass
from typing import Tuple
from multiaddr import Multiaddr


@dataclass(slots=True, frozen=True)
class NetworkAddress:
    """
    Network address wrapper using Multiaddr for protocol-aware addressing.

    Provides a consistent interface for handling addresses across
    the BitTorrent and DHT implementations with proper protocol specification.
    """

    _multiaddr: Multiaddr

    def __init__(self, host: str, port: int, protocol: str = "tcp") -> None:
        # Validate protocol first
        if protocol not in ["tcp", "udp"]:
            raise ValueError(f"Protocol must be 'tcp' or 'udp', got {protocol}")

        # Validate port - UDP allows 0 for dynamic assignment, TCP requires > 0
        if protocol == "tcp" and not (1 <= port <= 65535):
            raise ValueError(f"TCP port must be between 1 and 65535, got {port}")
        elif protocol == "udp" and not (0 <= port <= 65535):
            raise ValueError(f"UDP port must be between 0 and 65535, got {port}")

        # Determine IP version and create multiaddr
        try:
            # Clean host for IPv6 bracket notation
            clean_host = host.strip("[]")

            # Detect IPv6: contains colon and not already bracketed
            if ":" in clean_host:
                multiaddr_str = f"/ip6/{clean_host}/{protocol}/{port}"
            else:
                multiaddr_str = f"/ip4/{clean_host}/{protocol}/{port}"

            multiaddr_obj = Multiaddr(multiaddr_str)
        except Exception as e:
            raise ValueError(
                f"Invalid address {host}:{port} with protocol {protocol}: {e}"
            ) from e

        object.__setattr__(self, "_multiaddr", multiaddr_obj)

    @property
    def host(self) -> str:
        """Get the IP address as a string."""
        # Extract IP address from multiaddr string
        addr_str = str(self._multiaddr)
        parts = addr_str.split("/")

        for i, part in enumerate(parts):
            if part in ["ip4", "ip6"] and i + 1 < len(parts):
                return parts[i + 1]

        raise ValueError("No IP address found in multiaddr")

    @property
    def port(self) -> int:
        """Get the port number."""
        # Extract port from multiaddr string
        addr_str = str(self._multiaddr)
        parts = addr_str.split("/")

        for i, part in enumerate(parts):
            if part in ["tcp", "udp"] and i + 1 < len(parts):
                return int(parts[i + 1])

        raise ValueError("No port found in multiaddr")

    @property
    def protocol(self) -> str:
        """Get the transport protocol (tcp or udp)."""
        # Extract protocol from multiaddr string
        addr_str = str(self._multiaddr)
        parts = addr_str.split("/")

        for part in parts:
            if part in ["tcp", "udp"]:
                return part

        raise ValueError("No transport protocol found in multiaddr")

    @property
    def is_ipv4(self) -> bool:
        """Check if this is an IPv4 address."""
        return "/ip4/" in str(self._multiaddr)

    @property
    def is_ipv6(self) -> bool:
        """Check if this is an IPv6 address."""
        return "/ip6/" in str(self._multiaddr)

    @property
    def is_tcp(self) -> bool:
        """Check if this uses TCP protocol."""
        return self.protocol == "tcp"

    @property
    def is_udp(self) -> bool:
        """Check if this uses UDP protocol."""
        return self.protocol == "udp"

    @property
    def address_tuple(self) -> Tuple[str, int]:
        """Get the address as a (host, port) tuple."""
        return (self.host, self.port)

    @property
    def multiaddr(self) -> Multiaddr:
        """Get the underlying Multiaddr object."""
        return self._multiaddr

    def multiaddr_string(self, protocol: str) -> str:
        """Generate multiaddr string, optionally overriding protocol."""
        if protocol is None:
            return str(self._multiaddr)

        # Create new multiaddr with different protocol
        ip_proto = "ip6" if self.is_ipv6 else "ip4"
        return f"/{ip_proto}/{self.host}/{protocol}/{self.port}"

    @classmethod
    def from_string(cls, address: str, protocol: str = "tcp") -> "NetworkAddress":
        """Create NetworkAddress from 'host:port' string format."""
        if ":" not in address:
            raise ValueError("Address must be in 'host:port' format")

        # Handle IPv6 addresses with brackets
        if address.startswith("["):
            bracket_end = address.find("]")
            if bracket_end == -1:
                raise ValueError("Invalid IPv6 address format")
            host = address[1:bracket_end]
            port_str = address[bracket_end + 2 :]  # Skip ']:'
        else:
            host, port_str = address.rsplit(":", 1)

        try:
            port = int(port_str)
        except ValueError as e:
            raise ValueError(f"Invalid port: {port_str}") from e

        return cls(host, port, protocol)

    @classmethod
    def from_tuple(
        cls, address_tuple: Tuple[str, int], protocol: str = "tcp"
    ) -> "NetworkAddress":
        """Create NetworkAddress from (host, port) tuple."""
        host, port = address_tuple
        return cls(host, port, protocol)

    @staticmethod
    def is_valid_ip(host: str) -> bool:
        """Check if a string is a valid IP address."""
        try:
            # Try to create a multiaddr to validate
            if ":" in host and not host.startswith("["):
                Multiaddr(f"/ip6/{host}/tcp/80")
            else:
                clean_host = host.strip("[]")
                if ":" in clean_host:
                    Multiaddr(f"/ip6/{clean_host}/tcp/80")
                else:
                    Multiaddr(f"/ip4/{clean_host}/tcp/80")
            return True
        except Exception:
            return False

    @staticmethod
    def is_valid_port(port: int) -> bool:
        """Check if a port number is valid."""
        return 1 <= port <= 65535

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"

    def __repr__(self) -> str:
        return f"<NetworkAddress {self.protocol.upper()} {self.host}:{self.port}>"
