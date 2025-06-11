from typing import Optional, Set
from dataclasses import dataclass, field
from functools import cached_property
from multiaddr import Multiaddr

from id import PeerID
from network.address import NetworkAddress


@dataclass(slots=True)
class Peer:
    """
    BitTorrent Peer implementation.

    A peer is a BitTorrent client/server listening on TCP that implements
    the BitTorrent protocol for uploading/downloading files. This is separate
    from DHT nodes which operate on UDP for distributed hash table functionality.
    """

    peer_id: PeerID
    address: NetworkAddress
    active_torrents: Set[bytes] = field(default_factory=set)
    upload_rate: int = 0  # bytes/sec
    download_rate: int = 0  # bytes/sec
    is_seeder: bool = False
    capabilities: Set[str] = field(default_factory=set)  # BitTorrent extensions

    def __post_init__(self) -> None:
        """Validate the peer info after initialization."""
        # Validate that peers use TCP protocol
        if not self.address.is_tcp:
            raise ValueError("BitTorrent peers must use TCP protocol")

    @classmethod
    def create(cls, peer_id: PeerID, host: str, port: int, **kwargs) -> "Peer":
        """Create Peer with host/port strings (convenience method)."""
        address = NetworkAddress(host, port, protocol="tcp")
        return cls(peer_id, address, **kwargs)

    @property
    def host(self) -> str:
        """Get the host as a string."""
        return self.address.host

    @property
    def host_str(self) -> str:
        """Get the host as a string."""
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

    @cached_property
    def multiaddr(self) -> Multiaddr:
        """Get the peer's address as a Multiaddr."""
        return self.address.multiaddr

    def add_torrent(self, info_hash: bytes) -> None:
        """Add a torrent to the active torrents list."""
        self.active_torrents.add(info_hash)

    def remove_torrent(self, info_hash: bytes) -> None:
        """Remove a torrent from the active torrents list."""
        self.active_torrents.discard(info_hash)

    def has_torrent(self, info_hash: bytes) -> bool:
        """Check if peer has a specific torrent."""
        return info_hash in self.active_torrents

    def add_capability(self, capability: str) -> None:
        """Add a BitTorrent protocol capability/extension."""
        self.capabilities.add(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if peer supports a specific capability."""
        return capability in self.capabilities

    def __repr__(self) -> str:
        return f"<Peer {self.peer_id} {self.address}>"


@dataclass(slots=True, frozen=True)
class PeerInfo:
    """
    Lightweight peer information for BitTorrent protocol exchanges.

    Used for peer discovery, announcements, and tracking. This is the
    minimal information needed to identify and connect to a BitTorrent peer.
    """

    peer_id: PeerID
    address: NetworkAddress
    capabilities: Set[str] = field(default_factory=set)

    def __init__(
        self,
        peer_id: PeerID,
        address: NetworkAddress,
        capabilities: Optional[Set[str]] = None,
    ) -> None:
        # Validate that peers use TCP protocol
        if not address.is_tcp:
            raise ValueError("BitTorrent peers must use TCP protocol")

        object.__setattr__(self, "peer_id", peer_id)
        object.__setattr__(self, "address", address)
        object.__setattr__(self, "capabilities", capabilities or set())

    @classmethod
    def create(
        cls,
        peer_id: PeerID,
        host: str,
        port: int,
        capabilities: Optional[Set[str]] = None,
    ) -> "PeerInfo":
        """Create PeerInfo with host/port strings (convenience method)."""
        address = NetworkAddress(host, port, protocol="tcp")
        return cls(peer_id, address, capabilities)

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

    @cached_property
    def multiaddr(self) -> Multiaddr:
        """Get the peer's address as a Multiaddr."""
        return self.address.multiaddr

    def has_capability(self, capability: str) -> bool:
        """Check if peer supports a specific capability."""
        return capability in self.capabilities

    @classmethod
    def from_peer(cls, peer: Peer) -> "PeerInfo":
        """Create PeerInfo from a Peer instance."""
        return cls(
            peer_id=peer.peer_id,
            address=peer.address,
            capabilities=peer.capabilities.copy(),
        )

    def __repr__(self) -> str:
        return f"<PeerInfo {self.peer_id} {self.address}>"
