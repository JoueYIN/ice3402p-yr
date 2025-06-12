import os
import hashlib
import secrets
from typing import Union, BinaryIO
from dataclasses import dataclass

from id import ID


@dataclass
class FileID(ID):
    """
    160-bit File ID (InfoHash) for Mainline DHT protocol.

    Unlike NodeID which is randomly generated, FileID is a deterministic
    hash of file content used to locate file providers in the DHT network.
    """

    def __init__(self, id_input: Union[bytes, int, str, None] = None) -> None:
        """Initialize FileID with various input types.

        Args:
            id_input: Can be bytes, int, hex string, or None for random generation
        """
        if id_input is None:
            # Generate random 20-byte ID
            id_bytes = os.urandom(20)
        elif isinstance(id_input, bytes):
            if len(id_input) != 20:
                raise ValueError("FileID must be exactly 20 bytes")
            id_bytes = id_input
        elif isinstance(id_input, int):
            if id_input < 0 or id_input >= (1 << 160):
                raise ValueError("FileID must be a valid 160-bit unsigned integer")
            id_bytes = id_input.to_bytes(20, byteorder="big")
        elif isinstance(id_input, str):
            if len(id_input) != 40:
                raise ValueError("Invalid hex string: must be exactly 40 characters")
            try:
                id_bytes = bytes.fromhex(id_input)
            except ValueError:
                raise ValueError("Invalid hex string")
        else:
            raise TypeError("FileID must be bytes, int, hex string, or None")

        super(FileID, self).__init__(id_bytes)

    def __bytes__(self) -> bytes:
        """Convert FileID to bytes."""
        return bytes(self._bytes)

    def to_hex(self) -> str:
        """Get the file ID as a hex string."""
        return self._bytes.hex()

    def __repr__(self) -> str:
        return f"<FileID {self.to_hex()[:16]}...>"

    @staticmethod
    def is_valid_bytes(data: bytes) -> bool:
        """Check if bytes data is valid for FileID without creating an object."""
        return isinstance(data, bytes) and len(data) == 20

    @staticmethod
    def is_valid_int(value: int) -> bool:
        """Check if integer value is valid for FileID without creating an object."""
        return isinstance(value, int) and 0 <= value < (1 << 160)

    @staticmethod
    def is_valid_hex(hex_str: str) -> bool:
        """Check if hex string is valid for FileID without creating an object."""
        try:
            data = bytes.fromhex(hex_str)
            return len(data) == 20
        except ValueError:
            return False

    @classmethod
    def from_hex(cls, hex_str: str) -> "FileID":
        """Create FileID from hex string."""
        return cls(hex_str)

    @classmethod
    def from_data(cls, data: bytes) -> "FileID":
        """Create FileID by hashing arbitrary data (SHA-1)."""
        hash_obj = hashlib.sha1()
        hash_obj.update(data)
        return cls(hash_obj.digest())

    @classmethod
    def from_file(cls, file_path: str) -> "FileID":
        """Create FileID by hashing a file's content (SHA-1)."""
        hash_obj = hashlib.sha1()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
        except IOError as e:
            raise ValueError(f"Cannot read file {file_path}: {e}") from e
        return cls(hash_obj.digest())

    @classmethod
    def from_file_handle(cls, file_handle: BinaryIO) -> "FileID":
        """Create FileID by hashing a file handle's content (SHA-1)."""
        hash_obj = hashlib.sha1()
        original_position = file_handle.tell()
        file_handle.seek(0)
        try:
            for chunk in iter(lambda: file_handle.read(8192), b""):
                hash_obj.update(chunk)
        finally:
            file_handle.seek(original_position)
        return cls(hash_obj.digest())

    @classmethod
    def from_string(cls, text: str, encoding: str = "utf-8") -> "FileID":
        """Create FileID by hashing a string (SHA-1)."""
        return cls.from_data(text.encode(encoding))

    @classmethod
    def generate_random(cls) -> "FileID":
        """Generate a random FileID for testing purposes."""
        return cls(secrets.token_bytes(20))

    def __hash__(self) -> int:
        """Override dataclass hash to use base class implementation."""
        return super().__hash__()
