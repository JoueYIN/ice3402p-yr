from dataclasses import dataclass

from node.node_id import NodeID
from network.address import NetworkAddress


@dataclass(slots=True, frozen=True)
class NodeInfo:
    """Information about a DHT node."""

    node_id: NodeID
    address: NetworkAddress

    def __init__(
        self,
        node_id: NodeID,
        address: NetworkAddress,
    ) -> None:
        # Validate that DHT nodes use UDP protocol
        if not address.is_udp:
            raise ValueError("DHT nodes must use UDP protocol")

        object.__setattr__(self, "node_id", node_id)
        object.__setattr__(self, "address", address)

    @classmethod
    def create(
        cls,
        node_id: NodeID,
        host: str,
        port: int,
    ) -> "NodeInfo":
        """Create NodeInfo with host/port strings (convenience method)."""
        address = NetworkAddress(host, port, protocol="udp")
        return cls(node_id, address)

    @property
    def host(self) -> str:
        """Get the host as a string."""
        return self.address.host

    @property
    def host_str(self) -> str:
        """Get the host as a string (backward compatibility)."""
        return self.address.host

    @property
    def port(self) -> int:
        """Get the port."""
        return self.address.port

    @property
    def is_ipv6(self) -> bool:
        """Check if the host is an IPv6 address."""
        return self.address.is_ipv6

    @property
    def is_ipv4(self) -> bool:
        """Check if the host is an IPv4 address."""
        return self.address.is_ipv4

    def __repr__(self) -> str:
        return f"<NodeInfo {self.node_id} {self.address}>"
