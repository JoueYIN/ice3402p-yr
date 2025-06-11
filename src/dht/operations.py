from typing import List, Dict, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field

from node.node_base import Node
from node.node_info import NodeInfo
from node.node_id import NodeID
from peer.peer_base import PeerInfo
from file.file_id import FileID
from network.address import NetworkAddress
from .messages import KademliaMessage, MessageType

if TYPE_CHECKING:
    from dht.simulator import DHT_Simulator


@dataclass
class QueryContext:
    """Context for tracking node/value lookup queries."""

    target_id: NodeID
    contacted_nodes: Set[NodeID] = field(default_factory=set)
    closest_nodes: List[NodeInfo] = field(default_factory=list)
    concurrency: int = 3
    k: int = 8


class KademliaOperations:
    def __init__(self, node: Node, simulator: "DHT_Simulator"):
        self.node = node
        self.simulator = simulator
        self.pending_requests: Dict[str, float] = {}

    # ========== Message Creation ==========

    def create_ping_message(self, target_node: NodeInfo) -> KademliaMessage:
        """Create a PING message to check if node is online."""
        return KademliaMessage.create_ping(
            self.node.node_id.to_hex(), self.node.host, self.node.port
        )

    def create_find_node_message(
        self, target_node: NodeInfo, search_id: NodeID
    ) -> KademliaMessage:
        """Create a FIND_NODE message to locate nodes."""
        return KademliaMessage.create_find_node(
            self.node.node_id.to_hex(),
            self.node.host,
            self.node.port,
            search_id.to_hex(),
        )

    def create_find_value_message(
        self, target_node: NodeInfo, file_id: FileID
    ) -> KademliaMessage:
        """Create a FIND_VALUE message to locate file providers."""
        return KademliaMessage.create_find_value(
            self.node.node_id.to_hex(), self.node.host, self.node.port, file_id.to_hex()
        )

    def create_store_message(
        self, target_node: NodeInfo, file_id: FileID, peer_info: PeerInfo
    ) -> KademliaMessage:
        """Create a STORE message to publish file availability."""
        return KademliaMessage.create_store(
            self.node.node_id.to_hex(),
            self.node.host,
            self.node.port,
            file_id.to_hex(),
            peer_info.host,
            peer_info.port,
        )

    # ========== Message Handlers ==========

    def handle_ping(self, message: KademliaMessage) -> KademliaMessage:
        """Handle incoming PING request - update routing table and respond."""
        # Log the event
        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} received PING from {message.sender_id[:8]}"
            )

        # Passive node collection: Add sender to routing table
        sender_node = self._create_node_info_from_message(message)
        self.update_routing_table(sender_node)

        return KademliaMessage(
            message_type=MessageType.PING_RESPONSE,
            sender_id=self.node.node_id.to_hex(),
            sender_ip=self.node.host,
            sender_port=self.node.port,
            message_id=message.message_id,
            data={"status": "alive"},
        )

    def handle_find_node(self, message: KademliaMessage) -> KademliaMessage:
        """Handle incoming FIND_NODE request."""
        target_id = NodeID.from_hex(message.data["target_id"])

        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} received FIND_NODE for {target_id.to_hex()[:8]} from {message.sender_id[:8]}"
            )

        # Passive node collection: Add sender to routing table
        sender_node = self._create_node_info_from_message(message)
        self.update_routing_table(sender_node)

        # Find K closest nodes to target
        closest_nodes = self.node.find_closest_nodes(
            target_id, self.node.routing_table.k
        )

        return KademliaMessage(
            message_type=MessageType.FIND_NODE_RESPONSE,
            sender_id=self.node.node_id.to_hex(),
            sender_ip=self.node.host,
            sender_port=self.node.port,
            message_id=message.message_id,
            data={"nodes": [self._node_info_to_dict(node) for node in closest_nodes]},
        )

    def handle_find_value(self, message: KademliaMessage) -> KademliaMessage:
        """Handle incoming FIND_VALUE request."""
        file_id = FileID.from_hex(message.data["file_id"])

        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} received FIND_VALUE for file {file_id.to_hex()[:8]} from {message.sender_id[:8]}"
            )

        # Passive node collection: Add sender to routing table
        sender_node = self._create_node_info_from_message(message)
        self.update_routing_table(sender_node)

        # Check if we have the file
        peer_list = self.node.get_file_peers(file_id)

        if peer_list:
            if self.simulator:
                self.simulator.log_message(
                    f"Node {self.node.node_id.to_hex()[:8]} found {len(peer_list)} peers for file {file_id.to_hex()[:8]}"
                )
            return KademliaMessage(
                message_type=MessageType.FIND_VALUE_RESPONSE,
                sender_id=self.node.node_id.to_hex(),
                sender_ip=self.node.host,
                sender_port=self.node.port,
                message_id=message.message_id,
                data={
                    "found": True,
                    "peers": [self._peer_info_to_dict(peer) for peer in peer_list],
                },
            )
        else:
            # Return K closest nodes to file ID
            closest_nodes = self.node.find_closest_nodes_to_file(
                file_id, self.node.routing_table.k
            )
            return KademliaMessage(
                message_type=MessageType.FIND_VALUE_RESPONSE,
                sender_id=self.node.node_id.to_hex(),
                sender_ip=self.node.host,
                sender_port=self.node.port,
                message_id=message.message_id,
                data={
                    "found": False,
                    "nodes": [self._node_info_to_dict(node) for node in closest_nodes],
                },
            )

    def handle_store(self, message: KademliaMessage) -> KademliaMessage:
        """Handle incoming STORE request."""
        file_id = FileID.from_hex(message.data["file_id"])
        peer_ip = message.data["peer_ip"]
        peer_port = message.data["peer_port"]

        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} received STORE for file {file_id.to_hex()[:8]} from {message.sender_id[:8]}"
            )

        # Create PeerInfo - using sender_id as peer_id for simplicity
        from id import PeerID

        peer_id = PeerID(message.sender_id.encode())  # Convert sender_id to PeerID
        peer_address = NetworkAddress(peer_ip, peer_port, protocol="tcp")
        peer_info = PeerInfo(peer_id, peer_address)

        # Store the file-peer mapping
        self.node.add_file_peer(file_id, peer_info)

        if self.simulator:
            self.simulator.log_file_table_update(
                self.node.node_id, file_id, "ADD", peer_info
            )

        # Passive node collection: Add sender to routing table
        sender_node = self._create_node_info_from_message(message)
        self.update_routing_table(sender_node)

        return KademliaMessage(
            message_type=MessageType.STORE_RESPONSE,
            sender_id=self.node.node_id.to_hex(),
            sender_ip=self.node.host,
            sender_port=self.node.port,
            message_id=message.message_id,
            data={"status": "stored"},
        )

    # ========== Routing Table Update ==========

    def update_routing_table(self, node_info: NodeInfo) -> bool:
        """Update routing table following Kademlia specification."""
        # Don't add ourselves
        if node_info.node_id == self.node.node_id:
            return False

        # Log k-bucket update
        if self.simulator:
            self.simulator.log_bucket_update(
                self.node.node_id, node_info.node_id, "UPDATE"
            )

        return self.node.add_node(node_info)

    # ========== Network Operations ==========

    def join_network(self, bootstrap_node: NodeInfo) -> bool:
        """Join the Kademlia network using bootstrap node."""
        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} joining network via bootstrap {bootstrap_node.node_id.to_hex()[:8]}"
            )

        # Step 1: Add bootstrap node
        self.update_routing_table(bootstrap_node)

        # Step 2: Send FIND_NODE for our own ID to bootstrap
        find_message = self.create_find_node_message(bootstrap_node, self.node.node_id)
        if self.simulator:
            response = self.simulator.deliver_message(
                bootstrap_node.node_id, find_message
            )

            if response and response.message_type == MessageType.FIND_NODE_RESPONSE:
                # Process response and continue discovery
                discovered_nodes = self._parse_find_node_response(response)
                for node in discovered_nodes:
                    self.update_routing_table(node)

                # Continue finding nodes until we have a good routing table
                self._bootstrap_routing_table()
                return True

        return False

    def _bootstrap_routing_table(self) -> None:
        """Continue populating routing table after initial bootstrap."""
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations and self.node.routing_table_size < 50:
            # Get all known nodes
            all_nodes = self.node.routing_table.all_nodes
            if not all_nodes:
                break

            # Send FIND_NODE requests to nodes
            for node in all_nodes[:3]:  # Limit concurrency
                find_message = self.create_find_node_message(node, self.node.node_id)
                if self.simulator:
                    response = self.simulator.deliver_message(
                        node.node_id, find_message
                    )

                    if (
                        response
                        and response.message_type == MessageType.FIND_NODE_RESPONSE
                    ):
                        discovered_nodes = self._parse_find_node_response(response)
                        for discovered_node in discovered_nodes:
                            self.update_routing_table(discovered_node)

            iteration += 1

    # ========== Node Location ==========

    def locate_nodes(self, target_id: NodeID, k: int = 8) -> List[NodeInfo]:
        """Locate nodes closest to target ID using iterative deepening."""
        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} locating nodes for target {target_id.to_hex()[:8]}"
            )

        context = QueryContext(target_id=target_id, k=k)

        # Start with K closest nodes from routing table
        context.closest_nodes = self.node.find_closest_nodes(target_id, k)

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            # Select nodes to query (not yet contacted)
            nodes_to_query = [
                node
                for node in context.closest_nodes[:k]
                if node.node_id not in context.contacted_nodes
            ][: context.concurrency]

            if not nodes_to_query:
                break

            # Query nodes
            new_nodes_found = False
            for node in nodes_to_query:
                context.contacted_nodes.add(node.node_id)
                find_message = self.create_find_node_message(node, target_id)

                if self.simulator:
                    response = self.simulator.deliver_message(
                        node.node_id, find_message
                    )

                    if (
                        response
                        and response.message_type == MessageType.FIND_NODE_RESPONSE
                    ):
                        discovered_nodes = self._parse_find_node_response(response)
                        for discovered_node in discovered_nodes:
                            if discovered_node.node_id not in {
                                n.node_id for n in context.closest_nodes
                            }:
                                context.closest_nodes.append(discovered_node)
                                new_nodes_found = True

            if new_nodes_found:
                # Re-sort by distance to target
                context.closest_nodes.sort(
                    key=lambda n: target_id.xor_distance(n.node_id)
                )
                context.closest_nodes = context.closest_nodes[: k * 2]

            iteration += 1

        return context.closest_nodes[:k]

    # ========== File Location ==========

    def locate_file(
        self, file_id: FileID, k: int = 8
    ) -> tuple[List[PeerInfo], List[NodeInfo]]:
        """Locate file providers using FIND_VALUE requests."""
        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} locating file {file_id.to_hex()[:8]}"
            )

        # Convert FileID to NodeID for DHT lookup
        target_id = NodeID(file_id.to_bytes())
        context = QueryContext(target_id=target_id, k=k)
        found_peers: List[PeerInfo] = []

        # Start with closest nodes from routing table
        context.closest_nodes = self.node.find_closest_nodes_to_file(file_id, k)

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations and not found_peers:
            nodes_to_query = [
                node
                for node in context.closest_nodes[:k]
                if node.node_id not in context.contacted_nodes
            ][: context.concurrency]

            if not nodes_to_query:
                break

            # Query with FIND_VALUE
            for node in nodes_to_query:
                context.contacted_nodes.add(node.node_id)
                find_message = self.create_find_value_message(node, file_id)

                if self.simulator:
                    response = self.simulator.deliver_message(
                        node.node_id, find_message
                    )

                    if (
                        response
                        and response.message_type == MessageType.FIND_VALUE_RESPONSE
                    ):
                        if response.data.get("found", False):
                            # Found peers!
                            peer_data = response.data.get("peers", [])
                            for peer_dict in peer_data:
                                from id import PeerID

                                peer_id = PeerID(
                                    b"random_peer_id"
                                )  # Generate random for simulation
                                peer_address = NetworkAddress(
                                    peer_dict["ip"],
                                    int(peer_dict["port"]),
                                    protocol="tcp",
                                )
                                found_peers.append(PeerInfo(peer_id, peer_address))
                            break
                        else:
                            # Got more nodes to search
                            discovered_nodes = self._parse_find_node_response(response)
                            for discovered_node in discovered_nodes:
                                if discovered_node.node_id not in {
                                    n.node_id for n in context.closest_nodes
                                }:
                                    context.closest_nodes.append(discovered_node)

            # Re-sort closest nodes
            context.closest_nodes.sort(key=lambda n: target_id.xor_distance(n.node_id))
            context.closest_nodes = context.closest_nodes[: k * 2]
            iteration += 1

        return found_peers, context.closest_nodes[:k]

    # ========== File Publishing ==========

    def publish_file(self, file_id: FileID, peer_info: PeerInfo) -> bool:
        """Publish file availability to K closest nodes in the DHT."""
        if self.simulator:
            self.simulator.log_message(
                f"Node {self.node.node_id.to_hex()[:8]} publishing file {file_id.to_hex()[:8]}"
            )

        # Find K closest nodes to file ID
        closest_nodes = self.node.find_closest_nodes_to_file(
            file_id, self.node.routing_table.k
        )

        if not closest_nodes:
            return False

        success_count = 0
        for node in closest_nodes:
            store_message = self.create_store_message(node, file_id, peer_info)
            if self.simulator:
                response = self.simulator.deliver_message(node.node_id, store_message)
                if response and response.message_type == MessageType.STORE_RESPONSE:
                    success_count += 1

        return success_count > 0

    # ========== Helper Methods ==========

    def _create_node_info_from_message(self, message: KademliaMessage) -> NodeInfo:
        """Create NodeInfo from message sender information."""
        node_id = NodeID.from_hex(message.sender_id)
        address = NetworkAddress(message.sender_ip, message.sender_port, protocol="udp")
        return NodeInfo(node_id, address)

    def _node_info_to_dict(self, node_info: NodeInfo) -> Dict[str, str]:
        """Convert NodeInfo to dictionary for message serialization."""
        return {
            "node_id": node_info.node_id.to_hex(),
            "ip": node_info.host,
            "port": str(node_info.port),
        }

    def _peer_info_to_dict(self, peer_info: PeerInfo) -> Dict[str, str]:
        """Convert PeerInfo to dictionary for message serialization."""
        return {"ip": peer_info.host, "port": str(peer_info.port)}

    def _parse_find_node_response(self, response: KademliaMessage) -> List[NodeInfo]:
        """Parse FIND_NODE response and return list of NodeInfo objects."""
        nodes = []
        for node_dict in response.data.get("nodes", []):
            try:
                node_id = NodeID.from_hex(node_dict["node_id"])
                address = NetworkAddress(
                    node_dict["ip"], int(node_dict["port"]), protocol="udp"
                )
                nodes.append(NodeInfo(node_id, address))
            except (KeyError, ValueError):
                continue
        return nodes

    def handle_message(self, message: KademliaMessage) -> Optional[KademliaMessage]:
        """Route incoming messages to appropriate handlers."""
        handlers = {
            MessageType.PING: self.handle_ping,
            MessageType.FIND_NODE: self.handle_find_node,
            MessageType.FIND_VALUE: self.handle_find_value,
            MessageType.STORE: self.handle_store,
        }

        handler = handlers.get(message.message_type)
        if handler:
            return handler(message)

        return None
