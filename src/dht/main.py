#!/usr/bin/env python3
"""
Kademlia DHT Simulator

Usage:
    python -m dht.main <events_file>

Events file format (JSON):
[
    {
        "time": 100,
        "event": "NODE_JOIN",
        "params": {
            "nodeID": [array of 20 bytes],
            "address": [array of 6 bytes: 4-byte IP + 2-byte port]
        }
    },
    ...
]
"""

import sys
import json
import secrets
from typing import List, Dict, Any, Tuple

from dht.simulator import DHT_Simulator


def parse_events_file(filename: str) -> List[Tuple[int, str, Dict[str, Any]]]:
    """Parse events from JSON file."""
    with open(filename, "r") as f:
        events_data = json.load(f)

    events = []
    for event_data in events_data:
        time = event_data["time"]
        event_type = event_data["event"]
        params = event_data["params"]
        events.append((time, event_type, params))

    return events


def create_sample_events() -> List[Tuple[int, str, Dict[str, Any]]]:
    """Create sample simulation events for testing."""
    events = []

    # Node joins
    for i in range(5):
        node_id = secrets.token_bytes(20)
        address = [192, 168, 1, 100 + i, 0, 80 + i]  # IP + port
        events.append(
            (100 + i * 50, "NODE_JOIN", {"nodeID": list(node_id), "address": address})
        )

    # File publishing
    file_id = secrets.token_bytes(20)
    publisher_id = secrets.token_bytes(20)
    events.append(
        (
            400,
            "NODE_JOIN",
            {"nodeID": list(publisher_id), "address": [192, 168, 1, 200, 0, 90]},
        )
    )
    events.append(
        (450, "FILE_PUBLISH", {"nodeID": list(publisher_id), "fileID": list(file_id)})
    )

    # File retrieval
    retriever_id = secrets.token_bytes(20)
    events.append(
        (
            500,
            "NODE_JOIN",
            {"nodeID": list(retriever_id), "address": [192, 168, 1, 201, 0, 91]},
        )
    )
    events.append(
        (550, "FILE_RETRIEVE", {"nodeID": list(retriever_id), "fileID": list(file_id)})
    )

    return events


def main():
    """Main simulation runner."""
    # Create seed node
    seed_node_id = secrets.token_bytes(20)
    seed_address = [192, 168, 1, 1, 0, 80]  # 192.168.1.1:80

    # Initialize simulator
    simulator = DHT_Simulator(seed_node_id, bytes(seed_address))

    # Get events
    if len(sys.argv) > 1:
        events = parse_events_file(sys.argv[1])
    else:
        print("No events file provided, using sample events")
        events = create_sample_events()

    # Run simulation
    simulator.run_simulation(events)

    # Output results
    simulator.print_network_summary()
    simulator.dump_network_state("dht_final_state.json")
    simulator.save_log("dht_simulation.log")


if __name__ == "__main__":
    main()
