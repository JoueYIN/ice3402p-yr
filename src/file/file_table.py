import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
import asyncio

from file.file_id import FileID
from file.file_info import FileInfo

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from peer.peer_base import PeerInfo


@dataclass(slots=True)
class FileTable:
    """
    Hash table for storing FileID to BitTorrent peers mappings.

    This is separate from the DHT routing table and stores information about
    which BitTorrent peers have which files. The DHT is used to find this
    information, but the peers themselves are not DHT nodes.
    """

    files: Dict[FileID, FileInfo] = field(default_factory=dict)
    max_files: int = 10000
    cleanup_interval: int = 3600  # 1 hour
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def add_file_peer(
        self,
        file_id: FileID,
        peer_info: "PeerInfo",
        name: Optional[str] = None,
        size: Optional[int] = None,
    ) -> bool:
        """Add a BitTorrent peer as a provider for a specific file."""
        if file_id not in self.files:
            if len(self.files) >= self.max_files:
                self._cleanup_stale_files()
                if len(self.files) >= self.max_files:
                    return False  # Table is full

            self.files[file_id] = FileInfo(file_id=file_id, name=name, size=size)

        self.files[file_id].add_peer(peer_info)
        return True

    def remove_file_peer(self, file_id: FileID, peer_info: "PeerInfo") -> bool:
        """Remove a BitTorrent peer from a file's provider list."""
        if file_id in self.files:
            self.files[file_id].remove_peer(peer_info)

            # Remove file entry if no peers left
            if self.files[file_id].peer_count == 0:
                del self.files[file_id]

            return True
        return False

    def get_file_peers(self, file_id: FileID) -> List["PeerInfo"]:
        """Get all BitTorrent peers that have a specific file."""
        if file_id in self.files:
            return self.files[file_id].get_peers()
        return []

    def get_file_info(self, file_id: FileID) -> Optional[FileInfo]:
        """Get file information including metadata and peers."""
        return self.files.get(file_id)

    def has_file(self, file_id: FileID) -> bool:
        """Check if we have information about a specific file."""
        return file_id in self.files

    def get_all_files(self) -> List[FileID]:
        """Get all file IDs in the table."""
        return list(self.files.keys())

    def _cleanup_stale_files(self, max_age: int = 7200) -> int:
        """Remove stale file entries and return number of removed entries."""
        current_time = time.time()
        stale_files = [
            file_id
            for file_id, file_info in self.files.items()
            if current_time - file_info.last_updated > max_age
        ]

        for file_id in stale_files:
            del self.files[file_id]

        return len(stale_files)

    async def periodic_cleanup(self) -> None:
        """Periodically clean up stale file entries."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            async with self._lock:
                removed = self._cleanup_stale_files()
                if removed > 0:
                    print(f"Cleaned up {removed} stale file entries")

    @property
    def size(self) -> int:
        """Get the number of files in the table."""
        return len(self.files)

    @property
    def total_peers(self) -> int:
        """Get the total number of peer entries across all files."""
        return sum(file_info.peer_count for file_info in self.files.values())

    def get_stats(self) -> Dict[str, int]:
        """Get table statistics."""
        return {
            "total_files": self.size,
            "total_peers": self.total_peers,
            "max_capacity": self.max_files,
            "usage_percent": int((self.size / self.max_files) * 100),
        }

    def __repr__(self) -> str:
        return f"<FileTable files={self.size} peers={self.total_peers}>"
