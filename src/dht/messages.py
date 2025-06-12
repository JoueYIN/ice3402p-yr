from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
import json
import uuid


class MessageType(Enum):
    PING = "PING"
    STORE = "STORE"
    FIND_NODE = "FIND_NODE"
    FIND_VALUE = "FIND_VALUE"
    PING_RESPONSE = "PING_RESPONSE"
    STORE_RESPONSE = "STORE_RESPONSE"
    FIND_NODE_RESPONSE = "FIND_NODE_RESPONSE"
    FIND_VALUE_RESPONSE = "FIND_VALUE_RESPONSE"


@dataclass
class KademliaMessage:
    message_type: MessageType
    sender_id: str
    sender_ip: str
    sender_port: int
    message_id: str
    data: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(
            {
                "message_type": self.message_type.value,
                "sender_id": self.sender_id,
                "sender_ip": self.sender_ip,
                "sender_port": self.sender_port,
                "message_id": self.message_id,
                "data": self.data,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "KademliaMessage":
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            sender_ip=data["sender_ip"],
            sender_port=data["sender_port"],
            message_id=data["message_id"],
            data=data["data"],
        )

    @classmethod
    def create_ping(
        cls, sender_id: str, sender_ip: str, sender_port: int
    ) -> "KademliaMessage":
        return cls(
            message_type=MessageType.PING,
            sender_id=sender_id,
            sender_ip=sender_ip,
            sender_port=sender_port,
            message_id=str(uuid.uuid4()),
            data={},
        )

    @classmethod
    def create_find_node(
        cls, sender_id: str, sender_ip: str, sender_port: int, target_id: str
    ) -> "KademliaMessage":
        return cls(
            message_type=MessageType.FIND_NODE,
            sender_id=sender_id,
            sender_ip=sender_ip,
            sender_port=sender_port,
            message_id=str(uuid.uuid4()),
            data={"target_id": target_id},
        )

    @classmethod
    def create_find_value(
        cls, sender_id: str, sender_ip: str, sender_port: int, file_id: str
    ) -> "KademliaMessage":
        return cls(
            message_type=MessageType.FIND_VALUE,
            sender_id=sender_id,
            sender_ip=sender_ip,
            sender_port=sender_port,
            message_id=str(uuid.uuid4()),
            data={"file_id": file_id},
        )

    @classmethod
    def create_store(
        cls,
        sender_id: str,
        sender_ip: str,
        sender_port: int,
        file_id: str,
        peer_ip: str,
        peer_port: int,
    ) -> "KademliaMessage":
        return cls(
            message_type=MessageType.STORE,
            sender_id=sender_id,
            sender_ip=sender_ip,
            sender_port=sender_port,
            message_id=str(uuid.uuid4()),
            data={"file_id": file_id, "peer_ip": peer_ip, "peer_port": peer_port},
        )
