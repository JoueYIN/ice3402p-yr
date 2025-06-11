import time
import secrets
import asyncio
from typing import List, Optional, Dict, Callable, Awaitable
from dataclasses import dataclass, field
from functools import cached_property

from node.node_id import NodeID
from node.node_info import NodeInfo


@dataclass(slots=True)
class NodeEntry:
    """Entry in a K-bucket with additional metadata."""

    node_info: NodeInfo
    last_seen: float = field(default_factory=time.time)
    failed_count: int = 0

    @staticmethod
    def create_fresh(node_info: NodeInfo) -> "NodeEntry":
        """Create a fresh NodeEntry with current timestamp."""
        return NodeEntry(node_info, time.time(), 0)

    @staticmethod
    def is_stale_at_time(
        last_seen: float, current_time: float, timeout: int = 900
    ) -> bool:
        """Check if a node would be stale at a given time without creating an object."""
        return current_time - last_seen > timeout

    @property
    def is_stale(self) -> bool:
        """Check if node is considered stale (not seen for 15 minutes)."""
        return self.is_stale_at_time(self.last_seen, time.time())

    def mark_seen(self) -> None:
        """Mark the node as recently seen and reset failure count."""
        self.last_seen = time.time()
        self.failed_count = 0


@dataclass(slots=True)
class KBucket:
    """
    Kademlia K-bucket implementation for DHT routing table.
    Manages a list of nodes with a maximum size (k) and implements
    replacement strategy for stale nodes.
    """

    k: int = 8
    stale_timeout: int = 900  # 15 minutes
    nodes: List[NodeEntry] = field(default_factory=list)
    replacement_cache: List[NodeEntry] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)

    @staticmethod
    def calculate_bucket_index(node_id: NodeID, target_id: NodeID) -> int:
        """Calculate which bucket a target_id should go into relative to node_id."""
        distance = node_id.xor_distance(target_id)
        if distance == 0:
            return 0

        bit_length = distance.bit_length()
        return min(bit_length - 1, 159)

    @classmethod
    def create_with_capacity(cls, k: int, stale_timeout: int = 900) -> "KBucket":
        """Create a KBucket with specific capacity and timeout settings."""
        return cls(k=k, stale_timeout=stale_timeout)

    def get_node(self, node_id: NodeID) -> Optional[NodeEntry]:
        """Get a node entry by its ID. Returns None if not found."""
        return next(
            (entry for entry in self.nodes if entry.node_info.node_id == node_id), None
        )

    def add_node(self, node_info: NodeInfo) -> bool:
        """Add a node to the bucket with proper Kademlia replacement strategy."""
        # Update if node already exists
        if existing := self.get_node(node_info.node_id):
            existing.node_info = node_info
            existing.mark_seen()
            # Move to end (most recently seen)
            self.nodes.remove(existing)
            self.nodes.append(existing)
            self.last_updated = time.time()
            return True

        # Add new node if there's space
        if not self.is_full:
            entry = NodeEntry(node_info)
            self.nodes.append(entry)
            self.last_updated = time.time()
            return True

        # Bucket is full - add to replacement cache
        self._add_to_replacement_cache(NodeEntry(node_info))
        return False

    def _add_to_replacement_cache(self, entry: NodeEntry) -> None:
        """Add node to replacement cache, removing oldest if cache is full."""
        self.replacement_cache.append(entry)
        if len(self.replacement_cache) > self.k:
            self.replacement_cache.pop(0)

    def remove_node(self, node_id: NodeID) -> bool:
        """Remove a node from the bucket and try to replace with cached node."""
        for i, entry in enumerate(self.nodes):
            if entry.node_info.node_id == node_id:
                del self.nodes[i]
                self.last_updated = time.time()

                # Try to replace with node from replacement cache
                if self.replacement_cache:
                    replacement = self.replacement_cache.pop(0)
                    self.nodes.append(replacement)

                return True
        return False

    @cached_property
    def node_infos(self) -> List[NodeInfo]:
        """Get all node infos in the bucket (cached)."""
        return [entry.node_info for entry in self.nodes]

    def get_nodes(self) -> List[NodeInfo]:
        """Get all nodes in the bucket."""
        return [entry.node_info for entry in self.nodes]

    @property
    def oldest_node(self) -> Optional[NodeEntry]:
        """Get the least recently seen node."""
        return min(self.nodes, key=lambda x: x.last_seen, default=None)

    @property
    def is_full(self) -> bool:
        """Check if the bucket is full."""
        return len(self.nodes) >= self.k

    def mark_node_failed(self, node_id: NodeID) -> bool:
        """Mark a node as failed and remove if it exceeds failure threshold."""
        if entry := self.get_node(node_id):
            entry.failed_count += 1
            if entry.failed_count >= 3:
                return self.remove_node(node_id)
        return False

    def __len__(self) -> int:
        return len(self.nodes)


@dataclass(slots=True)
class RoutingTable:
    """
    DHT Routing Table implementation using K-buckets.
    Organizes nodes by XOR distance ranges in 160 buckets.
    """

    node_id: NodeID
    k: int = 8
    buckets: List[KBucket] = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @staticmethod
    def generate_random_id_in_bucket_range(
        node_id: NodeID, bucket_index: int
    ) -> NodeID:
        """Generate random ID that would fall into the specified bucket range."""
        if bucket_index == 0:
            return node_id

        random_distance = (1 << bucket_index) | secrets.randbits(bucket_index)
        target_int = node_id.int_value ^ random_distance
        return NodeID(target_int)

    @classmethod
    def create_with_config(cls, node_id: NodeID, k: int = 8) -> "RoutingTable":
        """Create a RoutingTable with specific configuration."""
        return cls(node_id=node_id, k=k)

    def __post_init__(self) -> None:
        """Initialize buckets after dataclass initialization."""
        self.buckets = [KBucket(self.k) for _ in range(160)]

    def _get_bucket_index(self, target_id: NodeID) -> int:
        """Get bucket index based on XOR distance."""
        distance = self.node_id.xor_distance(target_id)
        if distance == 0:
            return 0  # Should not happen for different nodes

        # Find the position of the highest set bit
        bit_length = distance.bit_length()
        return min(bit_length - 1, 159)

    def add_node(self, node_info: NodeInfo) -> bool:
        """Add a node to the appropriate bucket."""
        if node_info.node_id == self.node_id:
            return False  # Don't add ourselves

        bucket_index = self._get_bucket_index(node_info.node_id)
        bucket = self.buckets[bucket_index]
        return bucket.add_node(node_info)

    def remove_node(self, node_id: NodeID) -> bool:
        """Remove a node from the routing table."""
        bucket_index = self._get_bucket_index(node_id)
        return self.buckets[bucket_index].remove_node(node_id)

    def find_closest_nodes(self, target_id: NodeID, k: int = 8) -> List[NodeInfo]:
        """Find K closest nodes to target ID using XOR distance."""
        all_nodes = []
        for bucket in self.buckets:
            all_nodes.extend(bucket.get_nodes())

        # Sort by XOR distance to target
        all_nodes.sort(key=lambda node: target_id.xor_distance(node.node_id))
        return all_nodes[:k]

    def get_bucket_nodes(self, bucket_index: int) -> List[NodeInfo]:
        """Get all nodes from a specific bucket."""
        if 0 <= bucket_index < 160:
            return self.buckets[bucket_index].get_nodes()
        return []

    @property
    def all_nodes(self) -> List[NodeInfo]:
        """Get all nodes from all buckets."""
        all_nodes = []
        for bucket in self.buckets:
            all_nodes.extend(bucket.get_nodes())
        return all_nodes

    @property
    def size(self) -> int:
        """Get total number of nodes in routing table."""
        return sum(len(bucket) for bucket in self.buckets)

    @property
    def bucket_info(self) -> Dict[int, int]:
        """Get information about bucket sizes for debugging."""
        return {
            i: len(bucket) for i, bucket in enumerate(self.buckets) if len(bucket) > 0
        }

    def _generate_random_id_in_bucket(self, bucket_index: int) -> NodeID:
        """Generate random ID that would fall into the specified bucket."""
        return self.generate_random_id_in_bucket_range(self.node_id, bucket_index)

    async def refresh_buckets(
        self, lookup_func: Callable[[NodeID], Awaitable[None]]
    ) -> None:
        """Refresh stale buckets by performing lookups."""
        current_time = time.time()
        tasks = []

        for i, bucket in enumerate(self.buckets):
            if current_time - bucket.last_updated > 3600:  # 1 hour
                target_id = self._generate_random_id_in_bucket(i)
                tasks.append(lookup_func(target_id))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_node_timeout(self, node_id: NodeID) -> None:
        """Handle when a node times out during communication."""
        async with self._lock:
            bucket_index = self._get_bucket_index(node_id)
            bucket = self.buckets[bucket_index]
            bucket.mark_node_failed(node_id)
