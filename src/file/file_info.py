from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
import time

from file.file_id import FileID

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from peer.peer_base import PeerInfo


@dataclass(slots=True)
class FileInfo:
    """
    File information stored in DHT nodes.

    Contains file metadata and the set of BitTorrent peers that have this file.
    This is stored in DHT nodes but refers to BitTorrent peers, not DHT nodes.
    """

    file_id: FileID
    peers: List["PeerInfo"] = field(default_factory=list)
    name: Optional[str] = None
    size: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def add_peer(self, peer_info: "PeerInfo") -> None:
        """Add a BitTorrent peer that has this file."""
        if not self.has_peer(peer_info):
            self.peers.append(peer_info)
        self.last_updated = time.time()

    def remove_peer(self, peer_info: "PeerInfo") -> None:
        """Remove a BitTorrent peer from the file's peer set."""
        self.peers = [p for p in self.peers if p != peer_info]
        self.last_updated = time.time()

    def get_peers(self) -> List["PeerInfo"]:
        """Get all BitTorrent peers that have this file."""
        return list(self.peers)

    def has_peer(self, peer_info: "PeerInfo") -> bool:
        """Check if a specific BitTorrent peer has this file."""
        return peer_info in self.peers

    @property
    def peer_count(self) -> int:
        """Get the number of peers that have this file."""
        return len(self.peers)

    @property
    def is_stale(self) -> bool:
        """Check if file info is stale (not updated for specified timeout)."""
        timeout = 3600  # Default 1 hour timeout
        return time.time() - self.last_updated > timeout

    def __repr__(self) -> str:
        name_info = f" '{self.name}'" if self.name else ""
        return f"<FileInfo {self.file_id}{name_info} peers={self.peer_count}>"
