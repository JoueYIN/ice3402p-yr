from dataclasses import dataclass, field
from typing import List, Dict, Optional
from functools import cached_property

from peer.peer_base import PeerInfo
from node.node_id import NodeID
from node.node_info import NodeInfo
from bucket.kbucket import RoutingTable
from network.address import NetworkAddress
from file.file_table import FileTable
from file.file_id import FileID


@dataclass(slots=True)
class Node:
    """
    DHT Node implementation for Mainline DHT protocol.

    A node is a DHT client/server listening on UDP that implements
    the Mainline DHT protocol (variant of Kademlia DHT). This is completely
    separate from BitTorrent peers which handle file transfers over TCP.
    """

    node_id: NodeID = field(default_factory=NodeID.generate_random)
    address: NetworkAddress = field(
        default_factory=lambda: NetworkAddress("0.0.0.0", 0, protocol="udp")
    )
    routing_table: RoutingTable = field(init=False)
    file_table: FileTable = field(init=False)

    def __post_init__(self) -> None:
        """Initialize routing table and validate address after dataclass initialization."""
        # Validate that DHT nodes use UDP protocol
        if not self.address.is_udp:
            raise ValueError("DHT nodes must use UDP protocol")

        self.routing_table = RoutingTable(self.node_id, k=8)
        self.file_table = FileTable()

    @classmethod
    def create(
        cls,
        node_id: Optional[NodeID] = None,
        host: str = "0.0.0.0",
        port: int = 0,
    ) -> "Node":
        """Create Node with host/port strings (convenience method)."""
        if node_id is None:
            node_id = NodeID.generate_random()
        address = NetworkAddress(host, port, protocol="udp")
        return cls(node_id, address)

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
    def node_info(self) -> NodeInfo:
        """Get this node's NodeInfo."""
        return NodeInfo(self.node_id, self.address)

    def calculate_distance(self, target_node_id: NodeID) -> int:
        """Calculate XOR distance to target node."""
        return self.node_id.xor_distance(target_node_id)

    def add_node(self, node_info: NodeInfo) -> bool:
        """Add a DHT node to the routing table."""
        return self.routing_table.add_node(node_info)

    def find_closest_nodes(self, target_id: NodeID, k: int = 8) -> List[NodeInfo]:
        """Find K closest DHT nodes to target ID using XOR distance."""
        return self.routing_table.find_closest_nodes(target_id, k)

    def add_file_peer(
        self,
        file_id: FileID,
        peer_info: PeerInfo,
        name: Optional[str] = None,
        size: Optional[int] = None,
    ) -> bool:
        """
        Add a BitTorrent peer as a provider for a specific file.

        Note: This stores peer information for file sharing, not DHT routing.
        The peer_info contains BitTorrent peer details, not DHT node information.
        """
        return self.file_table.add_file_peer(file_id, peer_info, name, size)

    def get_file_peers(self, file_id: FileID) -> List[PeerInfo]:
        """Get all BitTorrent peers that have a specific file."""
        return self.file_table.get_file_peers(file_id)

    def find_closest_nodes_to_file(self, file_id: FileID, k: int = 8) -> List[NodeInfo]:
        """
        Find K closest DHT nodes to a file ID for publishing/retrieving file information.

        This uses the file ID as a target in the DHT keyspace to find nodes
        responsible for storing information about this file.
        """
        # Convert FileID to NodeID for DHT lookup - they both use 160-bit identifiers
        target_node_id = NodeID(file_id.to_bytes())
        return self.find_closest_nodes(target_node_id, k)

    @property
    def routing_table_size(self) -> int:
        """Get the total number of DHT nodes in routing table."""
        return self.routing_table.size

    @property
    def bucket_info(self) -> Dict[int, int]:
        """Get bucket size information for debugging."""
        return self.routing_table.bucket_info

    def __repr__(self) -> str:
        return f"<Node {self.node_id} {self.address}>"
