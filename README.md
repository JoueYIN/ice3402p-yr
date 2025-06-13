# Kademlia DHT Network Simulator

A comprehensive BitTorrent-like network simulator implementing a Kademlia-based Distributed Hash Table (DHT) algorithm.
This simulator processes event sequences to multiple operations in a simulated DHT network environment.

## Features

See [Report Slides](./report/slides.md) for a detailed overview.

This file also serves as a Slidev presentation, which can be viewed online at [Slidev Presentation](https://stackblitz.com/edit/github-8kygpu9u?file=slides.md).

## Requirements

- **Python**: >= 3.11
- **Dependencies**: Managed via `uv` or `pip` (see `pyproject.toml`)
  - `asyncio` for async operations
  - `base58` for peer ID encoding
  - `ipaddress` for network address handling
  - `multiaddr` for protocol-aware addressing

## Installation

### Using uv (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/JoueYIN/ice3402p-yr
   cd ice3402p-yr
   git switch dev
   ```

2. **Install with uv:**

   ```bash
   uv sync  # Install from uv.lock
   # OR
   uv pip install .  # Install from pyproject.toml
   ```

3. **For development:**

   ```bash
   uv pip install -e ".[test]"  # Install with test dependencies
   ```

### Using pip

1. **Set up virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install .
   # OR for development
   pip install -e ".[test]"
   ```

### Using Nix (For Nix Users)

```bash
nix develop  # Enter development shell with all dependencies
```

## User Manual

### Running the Simulator

#### Basic Usage

```bash
python -m dht.main [events_file.json]
```

If no events file is provided, the simulator runs with default sample events.

NOTE: If using uv, you may use `uv run` instead of `python` for each python command.

#### Example Commands

```bash
# Run with sample events
python -m dht.main sample_events.json

# Run with default events (if no file specified)
python -m dht.main
```

#### Supported Event Types

##### 1. NODE_JOIN

Adds a new DHT node to the network.

```json
{
  "time": 100,
  "event": "NODE_JOIN",
  "params": {
    "nodeID": [41, 22, 37, 218, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "address": [192, 168, 1, 100, 0, 80] // [IP1, IP2, IP3, IP4, PORT_HIGH, PORT_LOW]
  }
}
```

**Parameters:**

- `nodeID`: 20-byte array representing the 160-bit node identifier
- `address`: 6-byte array (4 bytes IPv4 + 2 bytes port in big-endian)

##### 2. NODE_LEAVE

Removes a DHT node from the network.

```json
{
  "time": 300,
  "event": "NODE_LEAVE",
  "params": {
    "nodeID": [41, 22, 37, 218, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  }
}
```

##### 3. FILE_PUBLISH

Publishes a file to the DHT (makes it available for download).

```json
{
  "time": 450,
  "event": "FILE_PUBLISH",
  "params": {
    "nodeID": [6, 63, 175, 93, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "fileID": [
      28, 144, 184, 136, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
  }
}
```

**Process:** The publishing node stores file information in the K closest DHT nodes to the file ID.

##### 4. FILE_RETRIEVE

Attempts to download a file from the DHT.

```json
{
  "time": 550,
  "event": "FILE_RETRIEVE",
  "params": {
    "nodeID": [
      138, 63, 224, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ],
    "fileID": [
      28, 144, 184, 136, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
  }
}
```

**Process:** The requesting node queries the DHT to find peers that have the file.

##### 5. PING

Tests connectivity between two DHT nodes.

```json
{
  "time": 125,
  "event": "PING",
  "params": {
    "sourceNodeID": [
      41, 22, 37, 218, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ],
    "targetNodeID": [
      44, 138, 213, 194, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
  }
}
```

### Output Files

The simulator generates comprehensive output for analysis:

#### 1. Console Output

Real-time logging of all simulation events, including:

- Node joins and leaves
- DHT message exchanges
- K-bucket updates
- File operations
- Network state changes

#### 2. `dht_simulation.log`

Detailed timestamped log file containing:

- All DHT protocol messages
- Routing table updates
- File table modifications
- Node discovery operations
- Error conditions and warnings

#### 3. `dht_final_state.json`

Complete network state snapshot including:

```json
{
  "simulation_time": 550,
  "total_nodes": 8,
  "message_statistics": {
    "FIND_NODE": 187,
    "PING": 6,
    "STORE": 6,
    "FIND_VALUE": 2
  },
  "nodes": [
    {
      "node_id": "2b2a799e87e81b148ab2db5a1acb08be5de72f77",
      "address": "192.168.1.1:80",
      "routing_table_size": 7,
      "bucket_info": {
        "153": 1,
        "155": 1,
        "157": 1,
        "158": 3,
        "159": 1
      },
      "file_table": {
        "1c90b88800000000000000000000000000000000": ["192.168.1.200:91"]
      }
    }
  ]
}
```

## Demo Usage

### Quick Start Demo

1. **Run the included sample:**

   ```bash
   python -m dht.main sample_events.json
   ```

2. **Watch the output:**
   - Console shows real-time simulation progress
   - Observe nodes joining and building routing tables
   - See file publishing and retrieval operations

### Understanding Sample Events

The `sample_events.json` demonstrates a complete DHT lifecycle:

1. **Network Bootstrapping** (t=100-400):

   - Multiple nodes join the network
   - Nodes discover each other through bootstrap process
   - Routing tables populate via FIND_NODE operations

2. **Network Maintenance** (t=125-525):

   - PING operations test node connectivity
   - K-bucket updates maintain routing table freshness

3. **File Sharing** (t=450-550):
   - Node publishes a file to the DHT
   - Another node successfully retrieves the file
   - STORE operations distribute file information
   - FIND_VALUE operations locate file providers

### Analyzing Results

#### Log Analysis

```bash
# View real-time events
tail -f dht_simulation.log

# Count message types
grep "Message" dht_simulation.log | cut -d' ' -f3 | sort | uniq -c

# Find specific operations
grep "FILE_PUBLISH\|FILE_RETRIEVE" dht_simulation.log
```

#### Network State Analysis

```bash
# View final state
cat dht_final_state.json | jq '.'

# Check node distribution
cat dht_final_state.json | jq '.nodes[].bucket_info'

# Analyze message statistics
cat dht_final_state.json | jq '.message_statistics'
```

### Custom Event Creation

Create your own event files to test specific scenarios:

```json
[
  {
    "time": 0,
    "event": "NODE_JOIN",
    "params": {
      "nodeID": [
        /* 20 bytes */
      ],
      "address": [192, 168, 1, 10, 31, 64] // 192.168.1.10:8000
    }
  },
  {
    "time": 100,
    "event": "FILE_PUBLISH",
    "params": {
      "nodeID": [
        /* publisher node ID */
      ],
      "fileID": [
        /* 20-byte file hash */
      ]
    }
  }
]
```

## Project Structure

```md
src/
├── dht/ # DHT protocol implementation
│ ├── simulator.py # Main simulation engine
│ ├── operations.py # Kademlia operations (join, publish, retrieve)
│ ├── messages.py # DHT message types and handlers
│ └── main.py # CLI entry point
├── node/ # DHT node implementation
│ ├── node_base.py # Core Node class with routing table
│ ├── node_id.py # 160-bit NodeID with XOR distance
│ └── node_info.py # NodeInfo data structure
├── peer/ # BitTorrent peer implementation
│ └── peer_base.py # Peer and PeerInfo classes
├── file/ # File handling and storage
│ ├── file_id.py # FileID (info hash) implementation
│ ├── file_info.py # File metadata and peer lists
│ └── file_table.py # File-to-peer mapping storage
├── bucket/ # Kademlia routing table
│ └── kbucket.py # K-bucket and RoutingTable classes
├── network/ # Network addressing
│ └── address.py # Protocol-aware network addresses
└── tests/ # Test suites for all modules
```

## API Reference

### Core Classes

#### `Node` (DHT Node)

```python
from node.node_base import Node

# Create a DHT node
node = Node.create(host="192.168.1.100", port=8000)

# Add other nodes to routing table
node.add_node(other_node_info)

# Find closest nodes to a target
closest = node.find_closest_nodes(target_id, k=8)
```

#### `FileID` (Info Hash)

```python
from file.file_id import FileID

# Create file ID from data
file_id = FileID.from_data(b"file content")

# Create from hex string
file_id = FileID.from_hex("a1b2c3d4...")

# Generate random ID
file_id = FileID.generate_random()
```

#### `RoutingTable` (Kademlia Routing)

```python
from bucket.kbucket import RoutingTable

# Create routing table
table = RoutingTable(node_id)

# Add nodes
table.add_node(node_info)

# Find closest nodes
closest = table.find_closest_nodes(target_id, k=8)
```

### Running Tests

```bash
# Run all tests
python -m pytest src/

# Run specific test file
python -m pytest src/file/test_file.py

# Run with coverage
python -m pytest --cov=src src/
```

## Advanced Usage

### Custom Simulation Parameters

Modify simulation behavior by editing the simulator configuration:

```python
# Custom K-bucket size
routing_table = RoutingTable(node_id, k=20)

# Custom file table capacity
file_table = FileTable(max_files=50000)

# Custom timeouts
bucket = KBucket(k=8, stale_timeout=1800)  # 30 minutes
```

### Network Analysis

The simulator provides rich data for network analysis:

```python
# Analyze routing table distribution
bucket_info = node.bucket_info
for bucket_idx, node_count in bucket_info.items():
    print(f"Bucket {bucket_idx}: {node_count} nodes")

# Check file distribution
file_peers = node.get_file_peers(file_id)
print(f"File has {len(file_peers)} peers")
```

## Troubleshooting

### Common Issues

1. **Empty target node ID in PING events**:

   - The sample events contain empty targetNodeID arrays
   - These represent invalid PING attempts and are handled gracefully

2. **Node not found errors**:

   - Normal behavior when referencing nodes that haven't joined yet
   - Check event ordering in your JSON file

3. **Import errors**:
   - Ensure you're running from the project root directory
   - Verify all dependencies are installed with `uv sync` or `pip install .`

### Performance Tuning

For large-scale simulations:

```python
# Increase capacities
routing_table = RoutingTable(node_id, k=32)
file_table = FileTable(max_files=100000)

# Reduce logging verbosity
# Edit simulator.py to adjust log levels
```

## Contributing

1. **Code Style**: Follow PEP 8, enforced by `ruff`
2. **Testing**: Add tests for new features
3. **Documentation**: Update docstrings and README
4. **Pre-commit**: Install pre-commit hooks with `pre-commit install`

## License

This project is licensed under MulanPSL-2.0. See the [LICENSE](LICENSE) file for details.
