import secrets
from typing import Union, Self


class NodeID(bytes):
    """A 160-bit node identifier for DHT nodes."""

    def __new__(cls, node_id: Union[bytes, int, str, None] = None) -> Self:
        """Create new NodeID instance."""
        if node_id is None:
            # Generate random 160-bit node ID
            node_bytes = secrets.token_bytes(20)
        elif isinstance(node_id, bytes):
            if len(node_id) != 20:
                raise ValueError("Node ID must be exactly 20 bytes (160 bits)")
            node_bytes = node_id
        elif isinstance(node_id, int):
            if node_id < 0 or node_id >= (1 << 160):
                raise ValueError("Node ID must be a 160-bit unsigned integer")
            node_bytes = node_id.to_bytes(20, byteorder="big")
        elif isinstance(node_id, str):
            # Treat string as hex representation
            try:
                node_bytes = bytes.fromhex(node_id)
                if len(node_bytes) != 20:
                    raise ValueError("Hex string must represent exactly 20 bytes")
            except ValueError as e:
                raise ValueError(f"Invalid hex string for NodeID: {node_id}") from e
        else:
            raise TypeError("Node ID must be bytes, int, hex string, or None")

        return super().__new__(cls, node_bytes)

    @property
    def int_value(self) -> int:
        """Get the NodeID as an integer."""
        return int.from_bytes(self, byteorder="big")

    def to_bytes(self) -> bytes:
        """Get the NodeID as bytes."""
        return bytes(self)

    def to_hex(self) -> str:
        """Get the node ID as a hex string."""
        return self.hex()

    def xor_distance(self, other: "NodeID") -> int:
        """
        Calculate XOR distance to another NodeID.

        This is the fundamental distance metric used in Kademlia DHT for:
        - Routing table organization (determining which bucket a node belongs to)
        - Finding closest nodes to a target ID
        - Determining responsibility for keys in the keyspace

        Args:
            other: Another NodeID to calculate distance to

        Returns:
            XOR distance as an integer
        """
        if not isinstance(other, NodeID):
            raise TypeError("Can only calculate XOR distance to another NodeID")

        # XOR the byte representations and convert to integer
        self_int = self.int_value
        other_int = other.int_value
        return self_int ^ other_int

    def common_prefix_length(self, other: "NodeID") -> int:
        """
        Calculate the number of common prefix bits with another NodeID.

        This is useful for determining how similar two NodeIDs are and
        which bucket they should be placed in.

        Args:
            other: Another NodeID to compare with

        Returns:
            Number of common prefix bits (0-160)
        """
        if not isinstance(other, NodeID):
            raise TypeError("Can only compare with another NodeID")

        distance = self.xor_distance(other)
        if distance == 0:
            return 160  # Identical IDs

        # Count leading zero bits in the XOR distance
        return 160 - distance.bit_length()

    def is_closer_to(self, target: "NodeID", other: "NodeID") -> bool:
        """
        Check if this NodeID is closer to target than another NodeID.

        Args:
            target: The target NodeID to compare distances to
            other: The other NodeID to compare against

        Returns:
            True if this NodeID is closer to target than other
        """
        self_distance = self.xor_distance(target)
        other_distance = other.xor_distance(target)
        return self_distance < other_distance

    def __repr__(self) -> str:
        return f"<NodeID {self.to_hex()[:16]}...>"

    @staticmethod
    def is_valid_bytes(data: bytes) -> bool:
        """Check if bytes data is valid for NodeID without creating an object."""
        return isinstance(data, bytes) and len(data) == 20

    @staticmethod
    def is_valid_int(value: int) -> bool:
        """Check if integer value is valid for NodeID without creating an object."""
        return isinstance(value, int) and 0 <= value < (1 << 160)

    @staticmethod
    def is_valid_hex(hex_str: str) -> bool:
        """Check if hex string is valid for NodeID without creating an object."""
        try:
            data = bytes.fromhex(hex_str)
            return len(data) == 20
        except ValueError:
            return False

    @classmethod
    def from_hex(cls, hex_str: str) -> "NodeID":
        """Create NodeID from hex string."""
        if not cls.is_valid_hex(hex_str):
            raise ValueError(f"Invalid hex string for NodeID: {hex_str}")
        return cls(hex_str)

    @classmethod
    def generate_random(cls) -> "NodeID":
        """Generate a random NodeID."""
        return cls()

    @classmethod
    def generate_random_in_range(cls, start: "NodeID", end: "NodeID") -> "NodeID":
        """Generate a random NodeID within a specific range."""
        start_int = start.int_value
        end_int = end.int_value
        if start_int >= end_int:
            raise ValueError("Start must be less than end")

        random_int = secrets.randbelow(end_int - start_int) + start_int
        return cls(random_int)
