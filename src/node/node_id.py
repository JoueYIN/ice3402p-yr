import secrets
from typing import Union
from dataclasses import dataclass

from id import ID


@dataclass(slots=True, frozen=True)
class NodeID(ID):
    """160-bit DHT Node ID for Mainline DHT protocol."""

    def __init__(self, node_id: Union[bytes, int, None] = None) -> None:
        if node_id is None:
            # Generate random 160-bit (20 bytes) node ID
            node_bytes = secrets.token_bytes(20)
        elif isinstance(node_id, bytes):
            if len(node_id) != 20:
                raise ValueError("Node ID must be exactly 20 bytes (160 bits)")
            node_bytes = node_id
        elif isinstance(node_id, int):
            if node_id < 0 or node_id >= (1 << 160):
                raise ValueError("Node ID must be a 160-bit unsigned integer")
            node_bytes = node_id.to_bytes(20, byteorder="big")
        else:
            raise TypeError("Node ID must be bytes, int, or None")

        super().__init__(node_bytes)

    def to_hex(self) -> str:
        """Get the node ID as a hex string."""
        return self._bytes.hex()

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
        node_bytes = bytes.fromhex(hex_str)
        return cls(node_bytes)

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

    def __hash__(self) -> int:
        """Override dataclass hash to use base class implementation."""
        return super().__hash__()
