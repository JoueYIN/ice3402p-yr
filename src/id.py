import hashlib
from typing import Union
from abc import ABC, abstractmethod
from functools import cached_property
import base58


class ID(ABC):
    """Base class for all ID types in the system."""

    _bytes: bytes

    def __init__(self, id_bytes: bytes) -> None:
        if not isinstance(id_bytes, bytes):
            raise TypeError("ID must be initialized with bytes")
        self._bytes = id_bytes

    @cached_property
    def int_value(self) -> int:
        """Get the ID as an integer for XOR distance calculations."""
        return int.from_bytes(self._bytes, byteorder="big")

    @property
    def xor_id(self) -> int:
        """Alias for int_value for backward compatibility."""
        return self.int_value

    def to_bytes(self) -> bytes:
        """Get the ID as bytes."""
        return self._bytes

    def xor_distance(self, other: "ID") -> int:
        """Calculate XOR distance between this ID and another ID."""
        return self.int_value ^ other.int_value

    def common_prefix_length(self, other: "ID") -> int:
        """Calculate the length of common prefix in bits."""
        distance = self.xor_distance(other)
        if distance == 0:
            return len(self._bytes) * 8
        return len(self._bytes) * 8 - distance.bit_length()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ID):
            return self._bytes == other._bytes
        elif isinstance(other, bytes):
            return self._bytes == other
        return False

    def __hash__(self) -> int:
        return hash(self._bytes)

    @abstractmethod
    def __repr__(self) -> str:
        pass


class PeerID:
    """Peer ID implementation with multihash support and base58 encoding."""

    _multihash: bytes
    _b58_str: str | None = None

    def __init__(self, multihash: bytes) -> None:
        """Initialize PeerID with multihash bytes."""
        if not isinstance(multihash, bytes):
            raise TypeError("PeerID must be initialized with multihash bytes")
        self._multihash = multihash

    @property
    def multihash(self) -> bytes:
        """Get the multihash bytes."""
        return self._multihash

    def to_bytes(self) -> bytes:
        """Get the multihash as bytes."""
        return self._multihash

    def to_base58(self) -> str:
        """Encode the multihash as base58 string."""
        if self._b58_str is None:
            self._b58_str = base58.b58encode(self._multihash).decode()
        return self._b58_str

    def __repr__(self) -> str:
        return f"<libp2p.peer.id.ID ({self.to_base58()})>"

    __str__ = pretty = to_string = to_base58

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PeerID):
            return self._multihash == other._multihash
        elif isinstance(other, str):
            return self.to_base58() == other
        elif isinstance(other, bytes):
            return self._multihash == other
        return False

    def __hash__(self) -> int:
        return hash(self._multihash)

    @classmethod
    def from_base58(cls, b58_encoded_peer_id_str: str) -> "PeerID":
        """Create PeerID from base58 encoded string."""
        peer_id_bytes = base58.b58decode(b58_encoded_peer_id_str)
        return cls(peer_id_bytes)

    @classmethod
    def from_pubkey(cls, pubkey: bytes, hash_func: str = "sha256") -> "PeerID":
        """Create PeerID from public key using specified hash function."""
        if hash_func == "sha256":
            hash_digest = hashlib.sha256(pubkey).digest()
            # Create multihash: <hash-type><hash-length><hash-digest>
            # SHA256 = 0x12, length = 32 bytes
            multihash = bytes([0x12, 0x20]) + hash_digest
        else:
            raise ValueError(f"Unsupported hash function: {hash_func}")
        return cls(multihash)


def sha256_digest(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf8")
    return hashlib.sha256(data).digest()
