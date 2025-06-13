---
# You can also start simply with 'default'
theme: default
# random image from a curated Unsplash collection by Anthony
# like them? see https://unsplash.com/collections/94734566/slidev
# some information about your slides (markdown enabled)
title: BitTorrent DHT Simulator Implementation
info: |
  ## Slidev Starter Template
  Presentation slides for developers.

  Learn more at [Sli.dev](https://sli.dev)
# apply unocss classes to the current slide
class: text-center
# https://sli.dev/features/drawing
drawings:
  persist: false
# slide transition: https://sli.dev/guide/animations.html#slide-transitions
transition: fade
# enable MDC Syntax: https://sli.dev/features/mdc
mdc: true
---

# BitTorrent DHT Simulator Implementation

Jun 13 2025

Yuxuan Sun, Rui Yin, Linrui Ma

---

# Intro

## Project Overview

This project implements a simulation of the BitTorrent Distributed Hash Table (DHT) network based on the Kademlia protocol.  
Nodes can join and leave dynamically, publish files, and locate peers through decentralized routing.

---

# Project Structure

```
src/
├── __init__.py               # Package initializer.
├── id.py                     # Handles node ID generation and XOR distance calculation.
├── test_id.py                # Unit tests for ID-related functionality.
├── bucket/                   # Implements Kademlia routing table using K-Buckets.
├── dht/                      # Core logic of the DHT simulator, including event processing and protocol operations.
├── file/                     # Manages file identifiers, metadata, and storage mappings in the DHT.
├── network/                  # Defines address representation and networking utilities (IP:port abstraction).
├── node/                     # Represents DHT nodes and their state, including node info and base logic.
├── peer/                     # Simulates peer-level behaviors such as seeding and retrieving files.
```

---

# Basic Implementation

- Seed Node & Network Initialization

Implemented in `dht/main.py`, the simulator initializes the network with a predefined seed node and time-driven event loop.

- Event Handling

Simulation events (e.g., node join, file publish/retrieve) are parsed and processed using a discrete-time tick system. This is orchestrated in `simulator.py`.

- DHT Operations

All four Kademlia operations (PING, STORE, FIND_NODE, FIND_VALUE) are implemented in `dht/operations.py` and invoked via simulated messages (`dht/messages.py`).

---

# Basic Implementation

- Routing Table Updates

Each node maintains a `bucket.KBucketTable`, which updates on incoming or outgoing messages as per Kademlia protocol.

- File Storage and Lookup

`file/` modules manage file publishing to nearest K nodes and retrieval by leechers, storing file info in hash tables per node.

- Output & Logging

Event logs and final DHT state (e.g. routing tables and file mappings) are exported to `dht_final_state.json`.

---

# Demo

<div class="overflow-y-scroll h-96">
```json
{
  "simulation_time": 550,
  "total_nodes": 8,
  "message_statistics": {
    "FIND_NODE": 187,
    "STORE": 6,
    "FIND_VALUE": 1
  },
  "nodes": [
    {
      "node_id": "e8d3f1179fadf92632671802bce8c7ee526d5324",
      "address": "192.168.1.1:80",
      "routing_table_size": 7,
      "bucket_info": {
        "153": 1,
        "156": 1,
        "157": 1,
        "159": 4
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "730e19b7bb5a9c8d9baf3d0a6bd4684adca81f9b",
      "address": "192.168.1.100:80",
      "routing_table_size": 6,
      "bucket_info": {
        "154": 1,
        "156": 1,
        "158": 1,
        "159": 3
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "d05fb69ef1c23dff203d948a3fe42c0e713d9de6",
      "address": "192.168.1.101:81",
      "routing_table_size": 5,
      "bucket_info": {
        "157": 3,
        "159": 2
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "ea441384d4b507e499a1ea0ad11b3becb0983887",
      "address": "192.168.1.102:82",
      "routing_table_size": 6,
      "bucket_info": {
        "153": 1,
        "156": 1,
        "157": 1,
        "159": 3
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "ff618fcf80e9faa4f9be7be9d5e39ff2e96071b9",
      "address": "192.168.1.103:83",
      "routing_table_size": 6,
      "bucket_info": {
        "156": 2,
        "157": 1,
        "159": 3
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "7679509b4246513ea461015ebb0ad3f6400beb43",
      "address": "192.168.1.104:84",
      "routing_table_size": 7,
      "bucket_info": {
        "154": 1,
        "156": 1,
        "158": 1,
        "159": 4
      },
      "file_table": {
        "414052c957a4ef19bcaa79d0fd39488c1469c585": ["192.168.1.200:91"]
      }
    },
    {
      "node_id": "04b8af5e63c677b1ad50b8e97ba6d47b0f799186",
      "address": "192.168.1.200:90",
      "routing_table_size": 7,
      "bucket_info": {
        "158": 3,
        "159": 4
      },
      "file_table": {}
    },
    {
      "node_id": "61f4394e877f065fff288b0047319ee95977300a",
      "address": "192.168.1.201:91",
      "routing_table_size": 7,
      "bucket_info": {
        "156": 2,
        "158": 1,
        "159": 4
      },
      "file_table": {}
    }
  ]
}
```
</div>

---

# What are our highlights?

---

# Optimizing DHT Storage with `@dataclass`

- `slots=True` for Memory Efficiency

  - Replaces `__dict__` with fixed `__slots__` in classes like `FileInfo`, `NodeEntry`, and `KBucket`.
  - Saves 20–50% memory per instance (critical for scaling with thousands of nodes/peers).
  - Faster attribute access (slot-based lookup vs. dictionary hashing).

- `frozen=True` for Immutability

  - Applied to `NetworkAddress` and `NodeInfo` to enforce thread-safe, hashable objects.
  - Enables safe use as dictionary keys (e.g., in routing tables) and caching optimizations.

- Combined Use Cases

  - `KBucket`/`NodeEntry`: `slots` reduces overhead in frequently updated routing tables.
  - `NetworkAddress`: `frozen` ensures protocol-safe addressing (no runtime modifications).

---

# Modular Testing with `pytest`

1. Isolated Component Testing

- `KBucket`: Validates routing logic (e.g., `test_add_node`, `test_remove_node`).
- `FileTable`/`FileInfo`: Ensures file-peer tracking accuracy (`test_add_file_peer`, `test_cleanup_stale_files`).
- `NodeID`/`PeerID`: Tests cryptographic ID generation and validation (`test_multihash_creation`, `test_id_equality`).

2. Fixtures for Reusable Context

- `sample_node_info`, `sample_file_id`: Standardize test data across 100+ test cases.
- Mock `Peer` objects simulate real peers without network overhead.

3. Edge Case Coverage

- Bucket overflow (`test_add_node_bucket_full`).
- Stale node cleanup (`test_cleanup_stale_files`).
- Invalid inputs (`test_init_invalid_bytes_length`).

---

# Impact on Reliability & Performance

## Quantifiable Improvements

| Metric               | Before pytest       | After pytest               |
| -------------------- | ------------------- | -------------------------- |
| **Routing Accuracy** | Manual verification | 100% `KBucket` coverage    |
| **Memory Leaks**     | Undetected          | Auto cleanup tests         |
| **ID Validation**    | Ad-hoc checks       | Rigorous `base58`/`SHA256` |

Why It Matters?

- Fault Tolerance: Tests like test_remove_nonexistent_node ensure graceful degradation.
- Performance: Mocked peers (sample_peer) enable fast, deterministic tests (~0.1s/test).
- Maintainability: Fixtures reduce boilerplate (e.g., reuse sample_node_info in 20+ tests).

---

# Unified IPv4 & IPv6 Address Support

## How It's Done

- Utilizes the [`Multiaddr`](https://multiformats.io/multiaddr/) standard to encode network addresses.
- Dynamically detects IP version:
  - e.g. `"/ip4/192.0.2.1/tcp/6881"` or `"/ip6/2001:db8::1/udp/6881"`
- Exposes rich interfaces:
  - `.is_ipv6`, `.is_ipv4`, `.protocol`, `.address_tuple`
  - Class methods: `from_string()`, `from_tuple()` for easy construction
- Validates IP/port and safely handles edge cases like `[IPv6]:port` notation.

## Why It Matters

- DHT networks are real-world Internet systems — supporting **both IPv4 and IPv6** is essential for realism and robustness.
- Our simulator fully supports both IP versions using **multi-protocol address abstraction**.

---

# PyPy Compatibility

JIT-Powered Performance Boost

## CPython

- Interprets bytecode
- Slow loops (~10x slower)
- GIL bottlenecks

## PyPy

- JIT compiles hot paths
- Optimized memory
- 4-10x faster for DHT

---

## layout: center

# Thank You!

## BitTorrent DHT Simulator
