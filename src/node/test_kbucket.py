import time
import pytest
from .node_id import NodeID
from .node_info import NodeInfo
from .kbucket import KBucket

@pytest.fixture
def sample_node_info():
    def _make(index):
        node_id = NodeID(index.to_bytes(20, byteorder="big"))
        return NodeInfo(node_id=node_id, host=f"192.168.0.{index}", port=6881 + index)
    return _make

def test_add_node(sample_node_info):
    bucket = KBucket(k=3)
    node1 = sample_node_info(1)
    result = bucket.add_node(node1)
    assert result is True
    assert len(bucket.nodes) == 1
    assert bucket.contains(node1.node_id)

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
    assert not bucket.contains(node.node_id)

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
    oldest = bucket.get_oldest_node()
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
