"""
Blockchain Mission Log for AirOne Professional v4.0
Implements an immutable, cryptographically verifiable ledger with JSON persistence.
"""
import logging
import hashlib
import time
import json
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float, data: Any, nonce: int = 0, hash: str = ""):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{json.dumps(self.data, sort_keys=True)}{self.nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine_block(self, difficulty: int):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce,
            "hash": self.hash
        }

class MissionBlockchain:
    def __init__(self, difficulty: int = 4, ledger_path: str = "logs/mission_ledger.json"):
        self.logger = logging.getLogger(f"{__name__}.MissionBlockchain")
        self.difficulty = difficulty
        self.ledger_path = ledger_path
        self.chain: List[Block] = []
        
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        self._load_ledger()

    def _load_ledger(self):
        """Loads the chain from disk or creates a genesis block."""
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'r') as f:
                    chain_data = json.load(f)
                    self.chain = [Block(**b) for b in chain_data]
                self.logger.info(f"Successfully loaded blockchain with {len(self.chain)} blocks.")
                if not self.is_chain_valid():
                    self.logger.critical("BLOCKCHAIN CORRUPTION DETECTED ON DISK!")
            except Exception as e:
                self.logger.error(f"Failed to load ledger: {e}. Starting fresh.")
                self._init_fresh_chain()
        else:
            self._init_fresh_chain()

    def _init_fresh_chain(self):
        genesis = Block(0, "0", time.time(), "Genesis Block - Mission Start")
        genesis.mine_block(self.difficulty)
        self.chain = [genesis]
        self._save_ledger()

    def _save_ledger(self):
        try:
            with open(self.ledger_path, 'w') as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save ledger: {e}")

    def add_event(self, event_data: Any) -> str:
        latest_block = self.chain[-1]
        new_block = Block(
            index=latest_block.index + 1,
            previous_hash=latest_block.hash,
            timestamp=time.time(),
            data=event_data
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self._save_ledger()
        self.logger.info(f"Event secured in Block {new_block.index}. Hash: {new_block.hash}")
        return new_block.hash

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]
            if current.hash != current.calculate_hash(): return False
            if current.previous_hash != prev.hash: return False
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bc = MissionBlockchain(difficulty=2)
    bc.add_event({"telemetry": "sample", "alt": 100})
    print(f"Chain valid: {bc.is_chain_valid()}")
