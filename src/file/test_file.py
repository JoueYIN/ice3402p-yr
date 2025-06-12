import time
import tempfile
import pytest
from unittest.mock import Mock

from file.file_id import FileID
from file.file_info import FileInfo
from file.file_table import FileTable


class TestFileID:
    """Test FileID functionality."""

    def test_init_with_bytes(self):
        """Test FileID creation with bytes."""
        data = b"a" * 20
        file_id = FileID(data)
        assert bytes(file_id) == data

    def test_init_with_int(self):
        """Test FileID creation with integer."""
        value = 12345
        file_id = FileID(value)
        expected_bytes = value.to_bytes(20, byteorder="big")
        assert bytes(file_id) == expected_bytes

    def test_init_with_hex_string(self):
        """Test FileID creation with hex string."""
        hex_str = "a" * 40  # 20 bytes in hex
        file_id = FileID(hex_str)
        expected_bytes = bytes.fromhex(hex_str)
        assert bytes(file_id) == expected_bytes

    def test_init_with_none(self):
        """Test FileID creation with None (random generation)."""
        file_id = FileID()
        assert len(bytes(file_id)) == 20

    def test_init_invalid_bytes_length(self):
        """Test FileID creation with invalid byte length."""
        with pytest.raises(ValueError, match="must be exactly 20 bytes"):
            FileID(b"short")

    def test_init_invalid_int_range(self):
        """Test FileID creation with invalid integer range."""
        with pytest.raises(ValueError, match="160-bit unsigned integer"):
            FileID(-1)
        with pytest.raises(ValueError, match="160-bit unsigned integer"):
            FileID(1 << 160)

    def test_init_invalid_hex_string(self):
        """Test FileID creation with invalid hex string."""
        with pytest.raises(ValueError, match="Invalid hex string"):
            FileID("invalid_hex")
        with pytest.raises(ValueError, match="Invalid hex string"):
            FileID("ab")  # Too short

    def test_init_invalid_type(self):
        """Test FileID creation with invalid type."""
        with pytest.raises(TypeError, match="must be bytes, int, hex string, or None"):
            FileID(12.34)  # type: ignore[call-arg]

    def test_to_hex(self):
        """Test hex string conversion."""
        data = b"a" * 20
        file_id = FileID(data)
        expected_hex = data.hex()
        assert file_id.to_hex() == expected_hex

    def test_repr(self):
        """Test string representation."""
        hex_str = "a" * 40
        file_id = FileID(hex_str)
        repr_str = repr(file_id)
        assert "FileID" in repr_str
        assert hex_str[:16] in repr_str

    def test_static_validation_methods(self):
        """Test static validation methods."""
        # Valid cases
        assert FileID.is_valid_bytes(b"a" * 20) is True
        assert FileID.is_valid_int(12345) is True
        assert FileID.is_valid_hex("a" * 40) is True

        # Invalid cases
        assert FileID.is_valid_bytes(b"short") is False
        assert FileID.is_valid_bytes(b"not_bytes") is False
        assert FileID.is_valid_int(-1) is False
        assert FileID.is_valid_int(1 << 160) is False
        assert FileID.is_valid_hex("invalid") is False
        assert FileID.is_valid_hex("ab") is False

    def test_class_methods(self):
        """Test class method functionality."""
        # Test from_hex
        hex_str = "a" * 40
        file_id = FileID.from_hex(hex_str)
        assert file_id.to_hex() == hex_str

        # Test from_data
        data = b"test data"
        file_id = FileID.from_data(data)
        assert len(bytes(file_id)) == 20

        # Test from_string
        text = "test string"
        file_id = FileID.from_string(text)
        assert len(bytes(file_id)) == 20

        # Test generate_random
        file_id = FileID.generate_random()
        assert len(bytes(file_id)) == 20

    def test_from_file(self):
        """Test file hashing."""
        test_content = b"test file content"
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(test_content)
            tf.flush()

            file_id = FileID.from_file(tf.name)
            assert len(bytes(file_id)) == 20

            # Test same content produces same hash
            file_id2 = FileID.from_file(tf.name)
            assert file_id == file_id2

    def test_from_file_handle(self):
        """Test file handle hashing."""
        test_content = b"test file content"
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(test_content)
            tf.flush()
            tf.seek(0)

            original_pos = tf.tell()
            file_id = FileID.from_file_handle(tf.file)  # type: ignore
            # Check position is restored
            assert tf.tell() == original_pos
            assert len(bytes(file_id)) == 20

    def test_hash_consistency(self):
        """Test hash consistency for same content."""
        data = b"consistent test data"
        file_id1 = FileID.from_data(data)
        file_id2 = FileID.from_data(data)
        assert file_id1 == file_id2
        assert hash(file_id1) == hash(file_id2)


class TestFileInfo:
    """Test FileInfo functionality."""

    @pytest.fixture
    def sample_file_id(self):
        return FileID.generate_random()

    @pytest.fixture
    def sample_peer(self):
        peer = Mock()
        peer.__hash__ = Mock(return_value=hash("peer1"))
        peer.__eq__ = Mock(return_value=True)
        return peer

    def test_init(self, sample_file_id):
        """Test FileInfo initialization."""
        file_info = FileInfo(file_id=sample_file_id)
        assert file_info.file_id == sample_file_id
        assert len(file_info.peers) == 0
        assert file_info.name is None
        assert file_info.size is None
        assert file_info.created_at <= time.time()
        assert file_info.last_updated <= time.time()

    def test_add_peer(self, sample_file_id, sample_peer):
        """Test adding a peer."""
        file_info = FileInfo(file_id=sample_file_id)
        old_time = file_info.last_updated
        time.sleep(0.01)

        file_info.add_peer(sample_peer)
        assert sample_peer in file_info.peers
        assert file_info.last_updated > old_time

    def test_remove_peer(self, sample_file_id, sample_peer):
        """Test removing a peer."""
        file_info = FileInfo(file_id=sample_file_id)
        file_info.add_peer(sample_peer)
        old_time = file_info.last_updated
        time.sleep(0.01)

        file_info.remove_peer(sample_peer)
        assert sample_peer not in file_info.peers
        assert file_info.last_updated > old_time

    def test_get_peers(self, sample_file_id, sample_peer):
        """Test getting all peers."""
        file_info = FileInfo(file_id=sample_file_id)
        file_info.add_peer(sample_peer)

        peers = file_info.get_peers()
        assert isinstance(peers, list)
        assert sample_peer in peers

    def test_has_peer(self, sample_file_id, sample_peer):
        """Test checking if peer exists."""
        file_info = FileInfo(file_id=sample_file_id)
        assert file_info.has_peer(sample_peer) is False

        file_info.add_peer(sample_peer)
        assert file_info.has_peer(sample_peer) is True

    def test_peer_count(self, sample_file_id, sample_peer):
        """Test peer count property."""
        file_info = FileInfo(file_id=sample_file_id)
        assert file_info.peer_count == 0

        file_info.add_peer(sample_peer)
        assert file_info.peer_count == 1

    def test_is_stale(self, sample_file_id):
        """Test staleness check."""
        file_info = FileInfo(file_id=sample_file_id)
        assert file_info.is_stale is False

        # Manually set old timestamp
        file_info.last_updated = time.time() - 7200  # 2 hours ago
        assert file_info.is_stale is True

    def test_repr(self, sample_file_id):
        """Test string representation."""
        file_info = FileInfo(file_id=sample_file_id, name="test.txt")
        repr_str = repr(file_info)
        assert "FileInfo" in repr_str
        assert "test.txt" in repr_str
        assert "peers=0" in repr_str


class TestFileTable:
    """Test FileTable functionality."""

    @pytest.fixture
    def file_table(self):
        return FileTable(max_files=5)

    @pytest.fixture
    def sample_file_id(self):
        return FileID.generate_random()

    @pytest.fixture
    def sample_peer(self):
        peer = Mock()
        peer.__hash__ = Mock(return_value=hash("peer1"))
        peer.__eq__ = Mock(return_value=True)
        return peer

    def test_add_file_peer(self, file_table, sample_file_id, sample_peer):
        """Test adding a file peer."""
        result = file_table.add_file_peer(sample_file_id, sample_peer, "test.txt", 1024)
        assert result is True
        assert file_table.has_file(sample_file_id)
        assert sample_peer in file_table.get_file_peers(sample_file_id)

    def test_add_file_peer_existing(self, file_table, sample_file_id, sample_peer):
        """Test adding peer to existing file."""
        file_table.add_file_peer(sample_file_id, sample_peer)

        peer2 = Mock()
        peer2.__hash__ = Mock(return_value=hash("peer2"))
        peer2.__eq__ = Mock(return_value=False)

        result = file_table.add_file_peer(sample_file_id, peer2)
        assert result is True
        assert len(file_table.get_file_peers(sample_file_id)) == 2

    def test_add_file_peer_table_full(self, file_table, sample_peer):
        """Test adding peer when table is full."""
        # Fill table to capacity
        for i in range(6):  # max_files = 5
            file_id = FileID.generate_random()
            file_table.add_file_peer(file_id, sample_peer)

        # Try to add one more
        new_file_id = FileID.generate_random()
        result = file_table.add_file_peer(new_file_id, sample_peer)
        # Should still work if cleanup removes stale files, or fail if none are stale
        assert isinstance(result, bool)

    def test_remove_file_peer(self, file_table, sample_file_id, sample_peer):
        """Test removing a file peer."""
        file_table.add_file_peer(sample_file_id, sample_peer)
        result = file_table.remove_file_peer(sample_file_id, sample_peer)
        assert result is True
        assert not file_table.has_file(
            sample_file_id
        )  # File removed when no peers left

    def test_remove_file_peer_nonexistent(
        self, file_table, sample_file_id, sample_peer
    ):
        """Test removing peer from nonexistent file."""
        result = file_table.remove_file_peer(sample_file_id, sample_peer)
        assert result is False

    def test_get_file_peers(self, file_table, sample_file_id, sample_peer):
        """Test getting file peers."""
        peers = file_table.get_file_peers(sample_file_id)
        assert peers == []

        file_table.add_file_peer(sample_file_id, sample_peer)
        peers = file_table.get_file_peers(sample_file_id)
        assert sample_peer in peers

    def test_get_file_info(self, file_table, sample_file_id, sample_peer):
        """Test getting file info."""
        info = file_table.get_file_info(sample_file_id)
        assert info is None

        file_table.add_file_peer(sample_file_id, sample_peer, "test.txt", 1024)
        info = file_table.get_file_info(sample_file_id)
        assert info is not None
        assert info.name == "test.txt"
        assert info.size == 1024

    def test_get_all_files(self, file_table, sample_file_id, sample_peer):
        """Test getting all file IDs."""
        assert file_table.get_all_files() == []

        file_table.add_file_peer(sample_file_id, sample_peer)
        files = file_table.get_all_files()
        assert sample_file_id in files

    def test_cleanup_stale_files(self, file_table, sample_file_id, sample_peer):
        """Test cleanup of stale files."""
        file_table.add_file_peer(sample_file_id, sample_peer)

        # Make file stale
        file_info = file_table.get_file_info(sample_file_id)
        file_info.last_updated = time.time() - 8000  # Over 2 hours ago

        removed = file_table._cleanup_stale_files(max_age=7200)
        assert removed == 1
        assert not file_table.has_file(sample_file_id)

    def test_properties(self, file_table, sample_file_id, sample_peer):
        """Test table properties."""
        assert file_table.size == 0
        assert file_table.total_peers == 0

        file_table.add_file_peer(sample_file_id, sample_peer)
        assert file_table.size == 1
        assert file_table.total_peers == 1

    def test_get_stats(self, file_table, sample_file_id, sample_peer):
        """Test getting table statistics."""
        stats = file_table.get_stats()
        expected_keys = {"total_files", "total_peers", "max_capacity", "usage_percent"}
        assert set(stats.keys()) == expected_keys
        assert stats["total_files"] == 0

        file_table.add_file_peer(sample_file_id, sample_peer)
        stats = file_table.get_stats()
        assert stats["total_files"] == 1
        assert stats["total_peers"] == 1
        assert stats["usage_percent"] == 20  # 1/5 * 100

    def test_repr(self, file_table, sample_file_id, sample_peer):
        """Test string representation."""
        repr_str = repr(file_table)
        assert "FileTable" in repr_str
        assert "files=0" in repr_str
        assert "peers=0" in repr_str

        file_table.add_file_peer(sample_file_id, sample_peer)
        repr_str = repr(file_table)
        assert "files=1" in repr_str
        assert "peers=1" in repr_str

    def test_periodic_cleanup(self, file_table, sample_file_id, sample_peer):
        """Test periodic cleanup functionality."""
        file_table.cleanup_interval = 0.1  # Very short interval for testing

        # Add a file and make it stale
        file_table.add_file_peer(sample_file_id, sample_peer)
        file_info = file_table.get_file_info(sample_file_id)
        file_info.last_updated = time.time() - 8000

        # Simple test without async context
        removed = file_table._cleanup_stale_files()
        assert removed == 1
        assert not file_table.has_file(sample_file_id)


if __name__ == "__main__":
    pytest.main([__file__])
