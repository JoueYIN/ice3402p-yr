import pytest
import base58
import hashlib
from id import PeerID, sha256_digest


def test_sha256_digest():
    # Test with string input
    test_str = "hello world"
    expected_hash = hashlib.sha256(test_str.encode("utf8")).digest()
    assert sha256_digest(test_str) == expected_hash

    # Test with bytes input
    test_bytes = b"hello world"
    assert sha256_digest(test_bytes) == expected_hash


def test_id_creation_from_bytes():
    test_bytes = b"test_peer_id_bytes"
    peer_id = PeerID(test_bytes)
    assert peer_id.to_bytes() == test_bytes


def test_id_creation_from_base58():
    test_bytes = b"test_peer_id_bytes"
    b58_str = base58.b58encode(test_bytes).decode()
    peer_id = PeerID.from_base58(b58_str)
    assert peer_id.to_bytes() == test_bytes
    assert peer_id.to_base58() == b58_str


def test_id_equality():
    test_bytes = b"test_peer_id_bytes"
    b58_str = base58.b58encode(test_bytes).decode()
    peer_id1 = PeerID(test_bytes)
    peer_id2 = PeerID.from_base58(b58_str)
    peer_id3 = PeerID(b"different_bytes")

    # Test equality with different types
    assert peer_id1 == peer_id2
    assert peer_id1 == test_bytes
    assert peer_id1 == b58_str
    assert peer_id1 != peer_id3
    assert peer_id1 != "invalid_string"
    assert peer_id1 != b"invalid_bytes"


def test_string_representations():
    test_bytes = b"test_repr_bytes"
    peer_id = PeerID(test_bytes)
    b58_str = base58.b58encode(test_bytes).decode()

    # Test all string representations
    assert str(peer_id) == b58_str
    assert peer_id.pretty() == b58_str
    assert peer_id.to_string() == b58_str
    assert peer_id.to_base58() == b58_str
    assert repr(peer_id) == f"<libp2p.peer.id.ID ({b58_str})>"


def test_hash():
    test_bytes = b"test_hash_bytes"
    peer_id = PeerID(test_bytes)

    # Hash should be consistent and based on the bytes
    expected_hash = hash(test_bytes)
    assert hash(peer_id) == expected_hash


def test_invalid_base58():
    with pytest.raises(Exception):
        PeerID.from_base58("invalid_base58_string")


def test_multihash_creation():
    """Test PeerID creation from public key with multihash."""
    pubkey = b"test_public_key_bytes"
    peer_id = PeerID.from_pubkey(pubkey)

    # Verify multihash structure
    multihash = peer_id.multihash
    assert multihash[0] == 0x12  # SHA256 hash type
    assert multihash[1] == 0x20  # 32 bytes length
    assert len(multihash) == 34  # 2 bytes header + 32 bytes hash


if __name__ == "__main__":
    pytest.main([__file__])
