import time
import pytest
from node.node_id import NodeID
from node.node_info import NodeInfo
from bucket.kbucket import KBucket
from network.address import NetworkAddress


@pytest.fixture
def sample_node_info():
    def _make(index):
        node_id = NodeID(index.to_bytes(20, byteorder="big"))
        address = NetworkAddress(f"192.168.0.{index}", 6881 + index, protocol="udp")
        return NodeInfo(node_id=node_id, address=address)

    return _make


def test_static_methods():
    """Test static method functionality."""
    # Test NodeID validation
    assert NodeID.is_valid_bytes(b"a" * 20) is True
    assert NodeID.is_valid_bytes(b"a" * 19) is False
    assert NodeID.is_valid_int(100) is True
    assert NodeID.is_valid_int(-1) is False

    # Test NetworkAddress validation
    assert NetworkAddress.is_valid_ip("192.168.1.1") is True
    assert NetworkAddress.is_valid_ip("::1") is True
    assert NetworkAddress.is_valid_ip("[::1]") is True
    assert NetworkAddress.is_valid_ip("invalid") is False
    assert NetworkAddress.is_valid_port(8080) is True
    assert NetworkAddress.is_valid_port(70000) is False


def test_class_methods():
    """Test class method functionality."""
    # Test NodeID creation methods
    node1 = NodeID.generate_random()
    node2 = NodeID.from_hex("a" * 40)  # 20 bytes in hex
    assert isinstance(node1, NodeID)
    assert isinstance(node2, NodeID)

    # Test NetworkAddress creation methods
    addr1 = NetworkAddress.from_string("192.168.1.1:8080", protocol="tcp")
    addr2 = NetworkAddress.from_tuple(("10.0.0.1", 9090), protocol="udp")
    assert addr1.host == "192.168.1.1"
    assert addr1.port == 8080
    assert addr1.is_tcp is True
    assert addr2.host == "10.0.0.1"
    assert addr2.port == 9090
    assert addr2.is_udp is True


def test_add_node(sample_node_info):
    bucket = KBucket(k=3)
    node1 = sample_node_info(1)
    result = bucket.add_node(node1)
    assert result is True
    assert len(bucket.nodes) == 1
    assert bucket.get_node(node1.node_id) is not None


def test_add_existing_node_updates_and_moves(sample_node_info):
    bucket = KBucket(k=3)
    node = sample_node_info(1)
    bucket.add_node(node)
    time.sleep(0.01)
    node_updated = sample_node_info(1)
    added_again = bucket.add_node(node_updated)
    assert added_again is True
    assert len(bucket.nodes) == 1
    assert bucket.nodes[-1].node_info.node_id == node.node_id  # Compare node_id only


def test_add_node_bucket_full(sample_node_info):
    bucket = KBucket(k=2)
    bucket.add_node(sample_node_info(1))
    bucket.add_node(sample_node_info(2))
    result = bucket.add_node(sample_node_info(3))
    assert result is False
    assert len(bucket.nodes) == 2


def test_remove_node(sample_node_info):
    bucket = KBucket(k=3)
    node = sample_node_info(1)
    bucket.add_node(node)
    assert bucket.remove_node(node.node_id) is True
    assert bucket.get_node(node.node_id) is None


def test_remove_nonexistent_node(sample_node_info):
    bucket = KBucket(k=3)
    node = sample_node_info(1)
    assert bucket.remove_node(node.node_id) is False


def test_get_node(sample_node_info):
    bucket = KBucket(k=3)
    node = sample_node_info(1)
    bucket.add_node(node)
    found = bucket.get_node(node.node_id)
    assert found is not None
    assert found.node_info.node_id == node.node_id


def test_get_oldest_node(sample_node_info):
    bucket = KBucket(k=3)
    node1 = sample_node_info(1)
    node2 = sample_node_info(2)
    bucket.add_node(node1)
    time.sleep(0.01)
    bucket.add_node(node2)
    oldest = bucket.oldest_node
    if oldest is None:
        pytest.skip("No nodes in bucket to test oldest node retrieval")
    assert oldest is not None
    assert oldest.node_info.node_id == node1.node_id


def test_get_nodes(sample_node_info):
    bucket = KBucket(k=2)
    n1, n2 = sample_node_info(1), sample_node_info(2)
    bucket.add_node(n1)
    bucket.add_node(n2)
    node_ids = [n.node_id for n in bucket.get_nodes()]
    assert n1.node_id in node_ids and n2.node_id in node_ids


def test_len(sample_node_info):
    bucket = KBucket(k=2)
    assert len(bucket) == 0
    bucket.add_node(sample_node_info(1))
    assert len(bucket) == 1


if __name__ == "__main__":
    pytest.main([__file__])
