"""
Blockchain Module - Full Implementation
Immutable telemetry logging and integrity verification
"""

import hashlib
import time
import json
from typing import Dict, List, Optional
from collections import deque


class Block:
    """Block in the blockchain"""
    
    def __init__(self, index: int, data: Dict, prev_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.data, sort_keys=True)}{self.prev_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine(self, difficulty: int = 2):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    """Blockchain for telemetry integrity"""
    
    def __init__(self, difficulty: int = 2):
        self.chain = [self.create_genesis()]
        self.difficulty = difficulty
    
    def create_genesis(self) -> Block:
        return Block(0, {"genesis": "true"}, "0")
    
    def add_block(self, data: Dict) -> Block:
        prev_block = self.chain[-1]
        new_block = Block(len(self.chain), data, prev_block.hash)
        new_block.mine(self.difficulty)
        self.chain.append(new_block)
        return new_block
    
    def get_block(self, index: int) -> Optional[Block]:
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            
            if curr.hash != curr.compute_hash():
                return False
            if curr.prev_hash != prev.hash:
                return False
        return True
    
    def get_chain_data(self) -> List[Dict]:
        return [{'index': b.index, 'timestamp': b.timestamp, 'data': b.data, 'hash': b.hash} for b in self.chain]


class SmartContract:
    """Simple smart contract for telemetry rules"""
    
    def __init__(self, name: str):
        self.name = name
        self.conditions = []
        self.actions = []
    
    def add_condition(self, condition: callable):
        self.conditions.append(condition)
    
    def add_action(self, action: str):
        self.actions.append(action)
    
    def execute(self, data: Dict) -> List[str]:
        for cond in self.conditions:
            if cond(data):
                return self.actions
        return []


class Transaction:
    """Transaction for data exchange"""
    
    def __init__(self, sender: str, receiver: str, data: Dict):
        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.timestamp = time.time()
        self.signature = None
    
    def sign(self, private_key: str):
        message = f"{self.sender}{self.receiver}{self.timestamp}"
        self.signature = hashlib.sha256((message + private_key).encode()).hexdigest()
    
    def verify(self, public_key: str) -> bool:
        if not self.signature:
            return False
        message = f"{self.sender}{self.receiver}{self.timestamp}"
        expected = hashlib.sha256((message + public_key).encode()).hexdigest()
        return self.signature == expected


if __name__ == "__main__":
    bc = Blockchain()
    bc.add_block({'altitude': 1000, 'temp': 25})
    bc.add_block({'altitude': 2000, 'temp': 20})
    print(f"Valid: {bc.is_valid()}")