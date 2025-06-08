import pytest
from .id import ID, sha256_digest
import base58
import hashlib

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
    peer_id = ID(test_bytes)
    assert peer_id.to_bytes() == test_bytes

def test_id_creation_from_base58():
    test_bytes = b"test_peer_id_bytes"
    b58_str = base58.b58encode(test_bytes).decode()
    peer_id = ID.from_base58(b58_str)
    assert peer_id.to_bytes() == test_bytes
    assert peer_id.to_base58() == b58_str

def test_id_equality():
    test_bytes = b"test_peer_id_bytes"
    b58_str = base58.b58encode(test_bytes).decode()
    peer_id1 = ID(test_bytes)
    peer_id2 = ID.from_base58(b58_str)
    peer_id3 = ID(b"different_bytes")
    
    # Test equality with different types
    assert peer_id1 == peer_id2
    assert peer_id1 == test_bytes
    assert peer_id1 == b58_str
    assert peer_id1 != peer_id3
    assert peer_id1 != "invalid_string"
    assert peer_id1 != b"invalid_bytes"

def test_xor_id_property():
    test_bytes = b"\x01\x02\x03"
    peer_id = ID(test_bytes)
    expected_xor = int.from_bytes(test_bytes, "big")
    assert peer_id.xor_id == expected_xor

def test_xor_distance():
    # Create two IDs with known XOR distance
    id1_bytes = b"\x00\x00\x00\x00"
    id2_bytes = b"\x00\x00\x00\xFF"
    
    id1 = ID(id1_bytes)
    id2 = ID(id2_bytes)
    
    # Calculate expected XOR distance
    expected_distance = int.from_bytes(b"\x00\x00\x00\xFF", byteorder="big")
    assert id1.xor_distance(id2) == expected_distance
    assert id2.xor_distance(id1) == expected_distance  # XOR distance is symmetric

def test_string_representations():
    test_bytes = b"test_repr_bytes"
    peer_id = ID(test_bytes)
    b58_str = base58.b58encode(test_bytes).decode()
    
    # Test all string representations
    assert str(peer_id) == b58_str
    assert peer_id.pretty() == b58_str
    assert peer_id.to_string() == b58_str
    assert peer_id.to_base58() == b58_str
    assert repr(peer_id) == f"<libp2p.peer.id.ID ({b58_str})>"

def test_hash():
    test_bytes = b"test_hash_bytes"
    peer_id = ID(test_bytes)
    
    # Hash should be consistent and based on the bytes
    expected_hash = hash(test_bytes)
    assert hash(peer_id) == expected_hash

def test_invalid_base58():
    with pytest.raises(Exception):
        ID.from_base58("invalid_base58_string")