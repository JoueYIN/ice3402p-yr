import hashlib
from typing import (
    Union,
)

import base58


class ID:
    _bytes: bytes
    _xor_id: int | None = None
    _b58_str: str | None = None

    def __init__(self, peer_id_bytes: bytes) -> None:
        self._bytes = peer_id_bytes

    @property
#    def xor_id(self) -> int:
#        if not self._xor_id:
#            self._xor_id = int(sha256_digest(self._bytes).hex(), 16)
#        return self._xor_id
    
    def xor_id(self) -> int:
        if not self._xor_id:
            # Kademlia 直接使用原始 ID 的 XOR
            self._xor_id = int.from_bytes(self._bytes, byteorder="big")
        return self._xor_id

    def xor_distance(self, other: "ID") -> int:
        """Calculate XOR distance between this ID and another ID."""
        return self.xor_id ^ other.xor_id

    def to_bytes(self) -> bytes:
        return self._bytes

    def to_base58(self) -> str:
        if not self._b58_str:
            self._b58_str = base58.b58encode(self._bytes).decode()
        return self._b58_str

    def __repr__(self) -> str:
        return f"<libp2p.peer.id.ID ({self!s})>"

    __str__ = pretty = to_string = to_base58

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.to_base58() == other
        elif isinstance(other, bytes):
            return self._bytes == other
        elif isinstance(other, ID):
            return self._bytes == other._bytes
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self._bytes)

    @classmethod
    def from_base58(cls, b58_encoded_peer_id_str: str) -> "ID":
        peer_id_bytes = base58.b58decode(b58_encoded_peer_id_str)
        pid = ID(peer_id_bytes)
        return pid


def sha256_digest(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf8")
    return hashlib.sha256(data).digest()
