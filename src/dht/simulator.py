import json
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from node.node_base import Node
from node.node_id import NodeID
from node.node_info import NodeInfo
from network.address import NetworkAddress
from file.file_id import FileID
from peer.peer_base import PeerID, PeerInfo
from .operations import KademliaOperations
from .messages import KademliaMessage


class EventType(Enum):
    NODE_JOIN = "NODE_JOIN"
    NODE_LEAVE = "NODE_LEAVE"
    FILE_PUBLISH = "FILE_PUBLISH"
    FILE_RETRIEVE = "FILE_RETRIEVE"
    PING = "PING"


@dataclass
class SimulationEvent:
    time: int
    event_type: EventType
    params: Dict[str, Any]


class DHT_Simulator:
    def __init__(
        self, seed_node_id: bytes, seed_address: bytes, tick_duration: float = 0.1
    ):
        """
        Initialize DHT simulator.

        Args:
            seed_node_id: 20-byte node ID
            seed_address: 6-byte address (4-byte IP + 2-byte port)
            tick_duration: Duration of each time tick in seconds (default 100ms)
        """
        self.current_time = 0
        self.tick_duration = tick_duration

        # Parse seed node address
        seed_ip = (
            f"{seed_address[0]}.{seed_address[1]}.{seed_address[2]}.{seed_address[3]}"
        )
        seed_port = (seed_address[4] << 8) | seed_address[5]

        # Create seed node
        seed_node_id_obj = NodeID(seed_node_id)
        seed_address_obj = NetworkAddress(seed_ip, seed_port, protocol="udp")
        self.seed_node = Node(seed_node_id_obj, seed_address_obj)

        # Initialize network state
        self.nodes: Dict[NodeID, Node] = {seed_node_id_obj: self.seed_node}
        self.operations: Dict[NodeID, KademliaOperations] = {
            seed_node_id_obj: KademliaOperations(self.seed_node, self)
        }

        # Event queue and logging
        self.event_queue: List[SimulationEvent] = []
        self.log_entries: List[str] = []

        # Statistics
        self.message_count = defaultdict(int)

        self.log_message(
            f"Seed node {seed_node_id_obj.to_hex()[:8]} initialized at {seed_ip}:{seed_port}"
        )

    def add_event(
        self, time: int, event_type: EventType, params: Dict[str, Any]
    ) -> None:
        """Add simulation event to the queue."""
        event = SimulationEvent(time, event_type, params)
        self.event_queue.append(event)
        # Keep queue sorted by time
        self.event_queue.sort(key=lambda e: e.time)

    def log_message(self, message: str) -> None:
        """Log a simulation message with timestamp."""
        log_entry = f"[{self.current_time:6d}] {message}"
        self.log_entries.append(log_entry)
        print(log_entry)

    def log_bucket_update(
        self, node_id: NodeID, target_id: NodeID, action: str
    ) -> None:
        """Log K-bucket update."""
        self.log_message(
            f"K-bucket update: Node {node_id.to_hex()[:8]} {action} {target_id.to_hex()[:8]}"
        )

    def log_file_table_update(
        self, node_id: NodeID, file_id: FileID, action: str, peer_info: PeerInfo
    ) -> None:
        """Log file table update."""
        self.log_message(
            f"File table update: Node {node_id.to_hex()[:8]} {action} file {file_id.to_hex()[:8]} -> {peer_info.host}:{peer_info.port}"
        )

    def deliver_message(
        self, target_node_id: NodeID, message: KademliaMessage
    ) -> Optional[KademliaMessage]:
        """Deliver message to target node and return response."""
        if target_node_id not in self.operations:
            return None

        # Log message delivery
        self.log_message(
            f"Message {message.message_type.value}: {message.sender_id[:8]} -> {target_node_id.to_hex()[:8]}"
        )
        self.message_count[message.message_type.value] += 1

        # Handle message and return response
        target_operations = self.operations[target_node_id]
        return target_operations.handle_message(message)

    def handle_node_join(self, params: Dict[str, Any]) -> None:
        """Handle node joining the network."""
        node_id_bytes = params["nodeID"]
        address_bytes = params["address"]

        # Parse address
        ip = f"{address_bytes[0]}.{address_bytes[1]}.{address_bytes[2]}.{address_bytes[3]}"
        port = (address_bytes[4] << 8) | address_bytes[5]

        # Create new node
        node_id = NodeID(bytes(node_id_bytes))
        address = NetworkAddress(ip, port, protocol="udp")
        new_node = Node(node_id, address)

        # Add to network
        self.nodes[node_id] = new_node
        self.operations[node_id] = KademliaOperations(new_node, self)

        self.log_message(f"Node {node_id.to_hex()[:8]} joining network at {ip}:{port}")

        # Join network through seed node
        seed_node_info = NodeInfo(self.seed_node.node_id, self.seed_node.address)
        success = self.operations[node_id].join_network(seed_node_info)

        if success:
            self.log_message(f"Node {node_id.to_hex()[:8]} successfully joined network")
        else:
            self.log_message(f"Node {node_id.to_hex()[:8]} failed to join network")

    def handle_node_leave(self, params: Dict[str, Any]) -> None:
        """Handle node leaving the network."""
        node_id_bytes = params["nodeID"]
        node_id = NodeID(node_id_bytes)

        if node_id in self.nodes:
            self.log_message(f"Node {node_id.to_hex()[:8]} leaving network")

            # Remove from all other nodes' routing tables
            for other_node_id, operations in self.operations.items():
                if other_node_id != node_id:
                    operations.node.routing_table.remove_node(node_id)

            # Remove from network
            del self.nodes[node_id]
            del self.operations[node_id]
        else:
            self.log_message(f"Node {node_id.to_hex()[:8]} not found for removal")

    def handle_file_publish(self, params: Dict[str, Any]) -> None:
        """Handle file publishing (seeding)."""
        node_id_bytes = params["nodeID"]
        file_id_bytes = params["fileID"]

        node_id = NodeID(bytes(node_id_bytes))
        file_id = FileID(bytes(file_id_bytes))

        if node_id not in self.operations:
            self.log_message(f"Publisher node {node_id.to_hex()[:8]} not found")
            return

        self.log_message(
            f"Node {node_id.to_hex()[:8]} publishing file {file_id.to_hex()[:8]}"
        )

        # Create peer info for the publishing node
        publisher_node = self.nodes[node_id]
        peer_id = PeerID(node_id.to_bytes())
        peer_address = NetworkAddress(
            publisher_node.host, publisher_node.port + 1, protocol="tcp"
        )  # Use different port for TCP
        peer_info = PeerInfo(peer_id, peer_address)

        # Publish file to DHT
        success = self.operations[node_id].publish_file(file_id, peer_info)

        if success:
            self.log_message(
                f"File {file_id.to_hex()[:8]} successfully published by {node_id.to_hex()[:8]}"
            )
        else:
            self.log_message(
                f"Failed to publish file {file_id.to_hex()[:8]} by {node_id.to_hex()[:8]}"
            )

    def handle_file_retrieve(self, params: Dict[str, Any]) -> None:
        """Handle file retrieval (leeching)."""
        node_id_bytes = params["nodeID"]
        file_id_bytes = params["fileID"]

        node_id = NodeID(bytes(node_id_bytes))
        file_id = FileID(bytes(file_id_bytes))

        if node_id not in self.operations:
            self.log_message(f"Retriever node {node_id.to_hex()[:8]} not found")
            return

        self.log_message(
            f"Node {node_id.to_hex()[:8]} retrieving file {file_id.to_hex()[:8]}"
        )

        # Locate file in DHT
        found_peers, closest_nodes = self.operations[node_id].locate_file(file_id)

        if found_peers:
            self.log_message(
                f"File {file_id.to_hex()[:8]} found! {len(found_peers)} peers available"
            )
            for peer in found_peers:
                self.log_message(f"  Peer: {peer.host}:{peer.port}")
        else:
            self.log_message(f"File {file_id.to_hex()[:8]} not found. Closest nodes:")
            for node in closest_nodes[:3]:  # Show top 3
                self.log_message(
                    f"  Node: {node.node_id.to_hex()[:8]} at {node.host}:{node.port}"
                )

    def handle_ping_event(self, params: Dict[str, Any]) -> None:
        """Handle explicit PING event between two nodes."""
        source_node_id_bytes = params["sourceNodeID"]
        target_node_id_bytes = params["targetNodeID"]

        source_node_id = NodeID(bytes(source_node_id_bytes))
        target_node_id = NodeID(bytes(target_node_id_bytes))

        if source_node_id not in self.operations:
            self.log_message(
                f"Source node {source_node_id.to_hex()[:8]} not found for PING"
            )
            return

        if target_node_id not in self.nodes:
            self.log_message(
                f"Target node {target_node_id.to_hex()[:8]} not found for PING"
            )
            return

        self.log_message(
            f"Node {source_node_id.to_hex()[:8]} pinging node {target_node_id.to_hex()[:8]}"
        )

        # Create PING message
        target_node_info = NodeInfo(target_node_id, self.nodes[target_node_id].address)
        ping_message = self.operations[source_node_id].create_ping_message(
            target_node_info
        )

        # Deliver PING message
        response = self.deliver_message(target_node_id, ping_message)

        if response and response.message_type.value == "PING_RESPONSE":
            self.log_message(
                f"Node {target_node_id.to_hex()[:8]} responded to PING from {source_node_id.to_hex()[:8]}"
            )
        else:
            self.log_message(
                f"No response to PING from {source_node_id.to_hex()[:8]} to {target_node_id.to_hex()[:8]}"
            )

    def run_simulation(self, events: List[Tuple[int, str, Dict[str, Any]]]) -> None:
        """Run the simulation with given events."""
        # Convert events to internal format
        for time, event_type_str, params in events:
            try:
                event_type = EventType(event_type_str)
                self.add_event(time, event_type, params)
            except ValueError:
                self.log_message(f"Unknown event type: {event_type_str}")

        self.log_message(f"Starting simulation with {len(self.event_queue)} events")

        # Process events in chronological order
        while self.event_queue:
            event = self.event_queue.pop(0)

            # Advance simulation time
            self.current_time = event.time
            self.log_message(f"Processing event: {event.event_type.value}")

            # Handle event
            if event.event_type == EventType.NODE_JOIN:
                self.handle_node_join(event.params)
            elif event.event_type == EventType.NODE_LEAVE:
                self.handle_node_leave(event.params)
            elif event.event_type == EventType.FILE_PUBLISH:
                self.handle_file_publish(event.params)
            elif event.event_type == EventType.FILE_RETRIEVE:
                self.handle_file_retrieve(event.params)
            elif event.event_type == EventType.PING:
                self.handle_ping_event(event.params)

        self.log_message("Simulation completed")

    def dump_network_state(self, filename: str) -> None:
        """Dump final network state to file."""
        state = {
            "simulation_time": self.current_time,
            "total_nodes": len(self.nodes),
            "message_statistics": dict(self.message_count),
            "nodes": [],
        }

        for node_id, node in self.nodes.items():
            node_state = {
                "node_id": node_id.to_hex(),
                "address": f"{node.host}:{node.port}",
                "routing_table_size": node.routing_table_size,
                "bucket_info": {str(k): v for k, v in node.bucket_info.items()},
                "file_table": {},
            }

            # Add file table information
            for file_id in node.file_table.get_all_files():
                peers = node.get_file_peers(file_id)
                node_state["file_table"][file_id.to_hex()] = [
                    f"{peer.host}:{peer.port}" for peer in peers
                ]

            state["nodes"].append(node_state)

        with open(filename, "w") as f:
            json.dump(state, f, indent=2)

        self.log_message(f"Network state dumped to {filename}")

    def save_log(self, filename: str) -> None:
        """Save simulation log to file."""
        with open(filename, "w") as f:
            for entry in self.log_entries:
                f.write(entry + "\n")

        self.log_message(f"Simulation log saved to {filename}")

    def print_network_summary(self) -> None:
        """Print summary of network state."""
        print(f"\n=== DHT Network Summary (Time: {self.current_time}) ===")
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Message statistics: {dict(self.message_count)}")

        print("\nNode details:")
        for node_id, node in self.nodes.items():
            print(f"  {node_id.to_hex()[:8]} at {node.host}:{node.port}")
            print(f"    Routing table: {node.routing_table_size} nodes")
            print(f"    File table: {node.file_table.size} files")

            # Show non-empty buckets
            bucket_info = node.bucket_info
            if bucket_info:
                print(f"    K-buckets: {bucket_info}")

            # Show files
            if node.file_table.size > 0:
                print("    Files:")
                for file_id in node.file_table.get_all_files():
                    peers = node.get_file_peers(file_id)
                    print(f"      {file_id.to_hex()[:8]}: {len(peers)} peers")
