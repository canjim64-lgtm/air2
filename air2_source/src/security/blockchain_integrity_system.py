"""
Blockchain-Based Integrity Verification System for AirOne Professional
Implements distributed ledger technology for data integrity and verification
"""

import hashlib
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import secrets
import asyncio
import aiohttp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import pickle
import os
from pathlib import Path
import requests
from functools import wraps


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Types of blockchain transactions"""
    DATA_INTEGRITY = "data_integrity"
    CONFIG_CHANGE = "config_change"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    AUDIT_LOG = "audit_log"
    SECURITY_EVENT = "security_event"


class BlockStatus(Enum):
    """Status of blockchain blocks"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    ORPHANED = "orphaned"


@dataclass
class Transaction:
    """Represents a blockchain transaction"""
    id: str
    timestamp: datetime
    transaction_type: TransactionType
    data: str  # JSON string of the actual data
    previous_hash: str
    nonce: int
    signature: str
    public_key: str
    node_id: str
    version: str = "1.0"


@dataclass
class Block:
    """Represents a blockchain block"""
    index: int
    timestamp: datetime
    transactions: List[Transaction]
    previous_hash: str
    nonce: int
    hash: str
    merkle_root: str
    validator_node: str
    status: BlockStatus = BlockStatus.VALID


class MerkleTree:
    """Implements Merkle tree for transaction verification"""
    
    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.tree = self._build_tree()
    
    def _build_tree(self) -> List[List[str]]:
        """Build the Merkle tree from transactions"""
        if not self.transactions:
            return []
        
        # Hash all transactions
        leaves = [self._hash_transaction(tx) for tx in self.transactions]
        
        # Build tree level by level
        tree = [leaves]
        
        while len(tree[-1]) > 1:
            level = tree[-1]
            next_level = []
            
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                
                combined = left + right
                next_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
            
            tree.append(next_level)
        
        return tree
    
    def _hash_transaction(self, transaction: Transaction) -> str:
        """Hash a transaction for the Merkle tree"""
        tx_data = f"{transaction.id}{transaction.timestamp.isoformat()}{transaction.transaction_type.value}{transaction.data}{transaction.previous_hash}{transaction.nonce}{transaction.node_id}"
        return hashlib.sha256(tx_data.encode('utf-8')).hexdigest()
    
    def get_root(self) -> str:
        """Get the Merkle root hash"""
        if not self.tree:
            return ""
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def verify_transaction(self, transaction: Transaction, proof: List[str], root: str) -> bool:
        """Verify a transaction against the Merkle root"""
        tx_hash = self._hash_transaction(transaction)
        current_hash = tx_hash
        
        for sibling_hash in proof:
            # Determine if sibling is left or right
            if hashlib.sha256((current_hash + sibling_hash).encode('utf-8')).hexdigest() == root or \
               hashlib.sha256((sibling_hash + current_hash).encode('utf-8')).hexdigest() == root:
                current_hash = hashlib.sha256((current_hash + sibling_hash).encode('utf-8')).hexdigest()
            else:
                # Try the other combination
                current_hash = hashlib.sha256((sibling_hash + current_hash).encode('utf-8')).hexdigest()
        
        return current_hash == root


class BlockchainNode:
    """Represents a node in the blockchain network"""
    
    def __init__(self, node_id: str, private_key: rsa.RSAPrivateKey = None):
        self.node_id = node_id
        self.private_key = private_key or rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.peers = set()
        self.transaction_pool = queue.Queue()
        self.blockchain = []
        self.lock = threading.Lock()
        self.difficulty = 4  # Number of leading zeros required
        self.target = 2 ** (256 - self.difficulty)
        
        # Initialize with genesis block
        if not self.blockchain:
            self._create_genesis_block()
        
        logger.info(f"Blockchain node {node_id} initialized")
    
    def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_tx = Transaction(
            id="genesis",
            timestamp=datetime.utcnow(),
            transaction_type=TransactionType.SYSTEM_EVENT,
            data=json.dumps({"message": "Genesis block"}),
            previous_hash="0" * 64,
            nonce=0,
            signature="",
            public_key=base64.b64encode(
                self.public_key.public_bytes(
                    encoding=base64.Encoding.PEM,
                    format=base64.PublicFormat.SubjectPublicKeyInfo
                )
            ).decode(),
            node_id=self.node_id
        )
        
        # Sign the transaction
        tx_hash = self._hash_transaction(genesis_tx)
        signature = self.private_key.sign(
            tx_hash.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        genesis_tx.signature = base64.b64encode(signature).decode()
        
        # Create genesis block
        genesis_block = Block(
            index=0,
            timestamp=datetime.utcnow(),
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            nonce=0,
            hash="",
            merkle_root="",
            validator_node=self.node_id
        )
        
        # Mine the genesis block
        self._mine_block(genesis_block)
        
        with self.lock:
            self.blockchain.append(genesis_block)
    
    def _hash_transaction(self, transaction: Transaction) -> str:
        """Hash a transaction"""
        tx_data = f"{transaction.id}{transaction.timestamp.isoformat()}{transaction.transaction_type.value}{transaction.data}{transaction.previous_hash}{transaction.nonce}{transaction.node_id}"
        return hashlib.sha256(tx_data.encode('utf-8')).hexdigest()
    
    def _hash_block(self, block: Block) -> str:
        """Hash a block"""
        block_data = f"{block.index}{block.timestamp.isoformat()}{len(block.transactions)}{block.previous_hash}{block.nonce}{block.validator_node}"
        return hashlib.sha256(block_data.encode('utf-8')).hexdigest()
    
    def _mine_block(self, block: Block):
        """Mine a block using Proof of Work"""
        target = 2 ** (256 - self.difficulty)
        nonce = 0
        
        # Calculate Merkle root
        merkle_tree = MerkleTree(block.transactions)
        block.merkle_root = merkle_tree.get_root()
        
        while True:
            block.nonce = nonce
            block.hash = self._calculate_block_hash(block)
            
            # Check if hash meets difficulty requirement
            if int(block.hash, 16) < target:
                break
            
            nonce += 1
            
            # Prevent infinite loop in case of issues
            if nonce > 10000000:  # Reasonable limit
                logger.warning(f"Block mining taking too long, increasing difficulty")
                self.difficulty += 1
                target = 2 ** (256 - self.difficulty)
                nonce = 0
    
    def _calculate_block_hash(self, block: Block) -> str:
        """Calculate block hash"""
        block_data = f"{block.index}{block.timestamp.isoformat()}{block.merkle_root}{block.previous_hash}{block.nonce}{block.validator_node}"
        return hashlib.sha256(block_data.encode('utf-8')).hexdigest()
    
    def add_transaction(self, transaction_type: TransactionType, data: Dict[str, Any]) -> str:
        """Add a transaction to the pool"""
        transaction = Transaction(
            id=secrets.token_urlsafe(16),
            timestamp=datetime.utcnow(),
            transaction_type=transaction_type,
            data=json.dumps(data),
            previous_hash=self.blockchain[-1].hash if self.blockchain else "0" * 64,
            nonce=0,
            signature="",
            public_key=base64.b64encode(
                self.public_key.public_bytes(
                    encoding=base64.Encoding.PEM,
                    format=base64.PublicFormat.SubjectPublicKeyInfo
                )
            ).decode(),
            node_id=self.node_id
        )
        
        # Sign the transaction
        tx_hash = self._hash_transaction(transaction)
        signature = self.private_key.sign(
            tx_hash.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        transaction.signature = base64.b64encode(signature).decode()
        
        # Verify the signature
        if not self._verify_transaction_signature(transaction):
            logger.error("Transaction signature verification failed")
            return None
        
        self.transaction_pool.put(transaction)
        logger.info(f"Transaction added to pool: {transaction.id}")
        return transaction.id
    
    def _verify_transaction_signature(self, transaction: Transaction) -> bool:
        """Verify transaction signature"""
        try:
            tx_hash = self._hash_transaction(transaction)
            signature = base64.b64decode(transaction.signature)
            public_key_pem = base64.b64decode(transaction.public_key)
            public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
            
            public_key.verify(
                signature,
                tx_hash.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def mine_block(self) -> Optional[Block]:
        """Mine a new block with pending transactions"""
        if self.transaction_pool.empty():
            logger.info("No transactions to mine")
            return None
        
        # Get pending transactions
        transactions = []
        while not self.transaction_pool.empty():
            try:
                tx = self.transaction_pool.get_nowait()
                if self._verify_transaction_signature(tx):
                    transactions.append(tx)
            except queue.Empty:
                break
        
        if not transactions:
            logger.info("No valid transactions to mine")
            return None
        
        # Create new block
        last_block = self.blockchain[-1]
        new_block = Block(
            index=last_block.index + 1,
            timestamp=datetime.utcnow(),
            transactions=transactions,
            previous_hash=last_block.hash,
            nonce=0,
            hash="",
            merkle_root="",
            validator_node=self.node_id
        )
        
        # Mine the block
        self._mine_block(new_block)
        
        # Add to blockchain
        with self.lock:
            self.blockchain.append(new_block)
        
        logger.info(f"Mined new block #{new_block.index} with {len(transactions)} transactions")
        return new_block
    
    def verify_blockchain(self) -> bool:
        """Verify the integrity of the entire blockchain"""
        for i in range(1, len(self.blockchain)):
            current_block = self.blockchain[i]
            previous_block = self.blockchain[i-1]
            
            # Verify block hash
            calculated_hash = self._calculate_block_hash(current_block)
            if calculated_hash != current_block.hash:
                logger.error(f"Block {i} hash verification failed")
                return False
            
            # Verify previous hash
            if previous_block.hash != current_block.previous_hash:
                logger.error(f"Block {i} previous hash verification failed")
                return False
        
        logger.info("Blockchain integrity verified successfully")
        return True
    
    def get_block_by_index(self, index: int) -> Optional[Block]:
        """Get a block by its index"""
        if 0 <= index < len(self.blockchain):
            return self.blockchain[index]
        return None
    
    def get_transaction_by_id(self, tx_id: str) -> Optional[Transaction]:
        """Get a transaction by its ID"""
        for block in self.blockchain:
            for tx in block.transactions:
                if tx.id == tx_id:
                    return tx
        return None
    
    def add_peer(self, peer_node_id: str):
        """Add a peer to the network"""
        self.peers.add(peer_node_id)
        logger.info(f"Added peer: {peer_node_id}")
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the latest block in the chain"""
        return self.blockchain[-1] if self.blockchain else None
    
    def get_blockchain_length(self) -> int:
        """Get the length of the blockchain"""
        return len(self.blockchain)


class IntegrityVerifier:
    """Verifies data integrity using blockchain technology"""
    
    def __init__(self, blockchain_node: BlockchainNode):
        self.node = blockchain_node
        self.verified_hashes = {}
        self.lock = threading.Lock()
        
        logger.info("Integrity verifier initialized")
    
    def record_data_hash(self, data: Any, data_type: str = "generic") -> str:
        """Record a data hash on the blockchain"""
        # Convert data to JSON string
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        
        # Calculate hash
        data_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        # Create transaction data
        tx_data = {
            "data_hash": data_hash,
            "data_type": data_type,
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": self.node.node_id
        }
        
        # Add transaction to blockchain
        tx_id = self.node.add_transaction(TransactionType.DATA_INTEGRITY, tx_data)
        
        if tx_id:
            with self.lock:
                self.verified_hashes[data_hash] = {
                    "tx_id": tx_id,
                    "timestamp": datetime.utcnow(),
                    "data_type": data_type
                }
            
            logger.info(f"Data hash recorded: {data_hash[:16]}... on blockchain")
            return data_hash
        else:
            logger.error("Failed to record data hash on blockchain")
            return None
    
    def verify_data_integrity(self, data: Any, expected_hash: str = None) -> Dict[str, Any]:
        """Verify the integrity of data against blockchain records"""
        # Convert data to JSON string
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        
        # Calculate current hash
        current_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        if expected_hash:
            # Compare with expected hash
            matches_expected = current_hash == expected_hash
        else:
            # Check if hash exists in our records
            matches_expected = current_hash in self.verified_hashes
        
        # Check blockchain for the hash
        blockchain_verified = False
        tx_details = None
        
        # Search blockchain for the hash
        for block in reversed(self.node.blockchain):  # Start from latest blocks
            for tx in block.transactions:
                if tx.transaction_type == TransactionType.DATA_INTEGRITY:
                    tx_data = json.loads(tx.data)
                    if tx_data.get("data_hash") == current_hash:
                        blockchain_verified = True
                        tx_details = {
                            "block_index": block.index,
                            "tx_id": tx.id,
                            "timestamp": tx_data.get("timestamp"),
                            "data_type": tx_data.get("data_type")
                        }
                        break
            if blockchain_verified:
                break
        
        result = {
            "current_hash": current_hash,
            "expected_hash": expected_hash,
            "matches_expected": matches_expected,
            "blockchain_verified": blockchain_verified,
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": self.node.node_id
        }
        
        if tx_details:
            result["blockchain_details"] = tx_details
        
        if matches_expected and blockchain_verified:
            logger.info(f"Data integrity verified: {current_hash[:16]}...")
        else:
            logger.warning(f"Data integrity check failed: {current_hash[:16]}...")
        
        return result
    
    def verify_hash_on_blockchain(self, data_hash: str) -> Dict[str, Any]:
        """Verify if a specific hash exists on the blockchain"""
        # Search blockchain for the hash
        for block in reversed(self.node.blockchain):
            for tx in block.transactions:
                if tx.transaction_type == TransactionType.DATA_INTEGRITY:
                    tx_data = json.loads(tx.data)
                    if tx_data.get("data_hash") == data_hash:
                        return {
                            "found": True,
                            "block_index": block.index,
                            "tx_id": tx.id,
                            "timestamp": tx_data.get("timestamp"),
                            "data_type": tx_data.get("data_type"),
                            "node_id": tx.node_id
                        }
        
        return {
            "found": False,
            "data_hash": data_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_verification_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get history of verification operations"""
        with self.lock:
            history = []
            for data_hash, details in list(self.verified_hashes.items())[-limit:]:
                history.append({
                    "data_hash": data_hash,
                    **details
                })
            return history


class BlockchainIntegritySystem:
    """Main system that orchestrates blockchain-based integrity verification"""
    
    def __init__(self, node_id: str = None, db_path: str = "./integrity.db"):
        self.node_id = node_id or f"node_{secrets.token_hex(8)}"
        self.node = BlockchainNode(self.node_id)
        self.verifier = IntegrityVerifier(self.node)
        self.db_path = db_path
        self.monitoring = False
        self.monitoring_thread = None
        
        # Initialize database
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_database()
        
        logger.info(f"Blockchain Integrity System initialized with node ID: {self.node_id}")
    
    def _init_database(self):
        """Initialize the integrity verification database"""
        cursor = self.db_conn.cursor()
        
        # Create integrity records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrity_records (
                id TEXT PRIMARY KEY,
                data_hash TEXT NOT NULL,
                data_type TEXT,
                blockchain_tx_id TEXT,
                verification_status TEXT,
                timestamp TEXT NOT NULL,
                node_id TEXT,
                metadata TEXT
            )
        """)
        
        # Create verification history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_history (
                id TEXT PRIMARY KEY,
                data_hash TEXT NOT NULL,
                verification_result TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                node_id TEXT,
                success BOOLEAN
            )
        """)
        
        # Create blockchain blocks table (for persistence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                id INTEGER PRIMARY KEY,
                index INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                transactions TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                validator_node TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_hash ON integrity_records(data_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON integrity_records(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_block_hash ON blockchain_blocks(hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_block_index ON blockchain_blocks(index)")
        
        self.db_conn.commit()
        logger.info("Integrity verification database initialized")
    
    def record_data_integrity(self, data: Any, data_type: str = "generic", 
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Record data integrity on the blockchain"""
        # Record the hash on blockchain
        data_hash = self.verifier.record_data_hash(data, data_type)
        
        if not data_hash:
            return {"success": False, "error": "Failed to record hash on blockchain"}
        
        # Store in database
        cursor = self.db_conn.cursor()
        record_id = f"integrity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        cursor.execute("""
            INSERT INTO integrity_records
            (id, data_hash, data_type, blockchain_tx_id, verification_status, timestamp, node_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id, data_hash, data_type, 
            self.verifier.verified_hashes[data_hash]["tx_id"],
            "recorded", datetime.utcnow().isoformat(),
            self.node_id, json.dumps(metadata or {})
        ))
        self.db_conn.commit()
        
        result = {
            "success": True,
            "data_hash": data_hash,
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": self.node_id,
            "blockchain_tx_id": self.verifier.verified_hashes[data_hash]["tx_id"]
        }
        
        logger.info(f"Data integrity recorded: {data_hash[:16]}...")
        return result
    
    def verify_data_integrity(self, data: Any, expected_hash: str = None) -> Dict[str, Any]:
        """Verify data integrity against blockchain records"""
        result = self.verifier.verify_data_integrity(data, expected_hash)
        
        # Store verification result in database
        cursor = self.db_conn.cursor()
        verification_id = f"verify_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        cursor.execute("""
            INSERT INTO verification_history
            (id, data_hash, verification_result, timestamp, node_id, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            verification_id, result["current_hash"], json.dumps(result),
            datetime.utcnow().isoformat(), self.node_id, result["matches_expected"]
        ))
        self.db_conn.commit()
        
        logger.info(f"Data integrity verification: {'SUCCESS' if result['matches_expected'] else 'FAILED'} - {result['current_hash'][:16]}...")
        return result
    
    def verify_hash_exists(self, data_hash: str) -> Dict[str, Any]:
        """Verify if a specific hash exists on the blockchain"""
        result = self.verifier.verify_hash_on_blockchain(data_hash)
        
        # Log the verification
        cursor = self.db_conn.cursor()
        verification_id = f"hash_verify_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        cursor.execute("""
            INSERT INTO verification_history
            (id, data_hash, verification_result, timestamp, node_id, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            verification_id, data_hash, json.dumps(result),
            datetime.utcnow().isoformat(), self.node_id, result["found"]
        ))
        self.db_conn.commit()
        
        return result
    
    def start_monitoring(self):
        """Start continuous integrity monitoring"""
        if self.monitoring:
            logger.warning("Integrity monitoring already running")
            return
        
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Integrity monitoring started")
    
    def stop_monitoring(self):
        """Stop integrity monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Integrity monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Periodically mine blocks if there are transactions
                if not self.node.transaction_pool.empty():
                    self.node.mine_block()
                
                # Verify blockchain integrity periodically
                if len(self.node.blockchain) > 1:  # Skip genesis block
                    is_valid = self.node.verify_blockchain()
                    if not is_valid:
                        logger.error("Blockchain integrity verification failed!")
                
                # Sleep before next iteration
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Get a comprehensive integrity report"""
        cursor = self.db_conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM integrity_records")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verification_history WHERE success = 1")
        successful_verifications = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verification_history WHERE success = 0")
        failed_verifications = cursor.fetchone()[0]
        
        # Get recent records
        cursor.execute("""
            SELECT data_hash, data_type, timestamp, verification_status 
            FROM integrity_records 
            ORDER BY timestamp DESC LIMIT 10
        """)
        recent_records = cursor.fetchall()
        
        # Get blockchain info
        blockchain_length = self.node.get_blockchain_length()
        latest_block = self.node.get_latest_block()
        
        return {
            "total_integrity_records": total_records,
            "successful_verifications": successful_verifications,
            "failed_verifications": failed_verifications,
            "blockchain_length": blockchain_length,
            "latest_block_index": latest_block.index if latest_block else 0,
            "latest_block_hash": latest_block.hash[:16] + "..." if latest_block else None,
            "recent_records": [
                {
                    "data_hash": record[0][:16] + "...",
                    "data_type": record[1],
                    "timestamp": record[2],
                    "status": record[3]
                } for record in recent_records
            ],
            "node_id": self.node_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_verification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get verification history"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT data_hash, verification_result, timestamp, success 
            FROM verification_history 
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "data_hash": row[0][:16] + "...",
                "verification_result": json.loads(row[1]),
                "timestamp": row[2],
                "success": row[3]
            })
        
        return results
    
    def add_data_with_verification(self, data: Any, data_type: str = "generic", 
                                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add data and immediately verify its integrity"""
        # Record the data
        record_result = self.record_data_integrity(data, data_type, metadata)
        
        if not record_result["success"]:
            return record_result
        
        # Verify the data
        verify_result = self.verify_data_integrity(data)
        
        return {
            **record_result,
            "verification_result": verify_result
        }
    
    def batch_verify_integrity(self, data_list: List[Any]) -> List[Dict[str, Any]]:
        """Batch verify integrity of multiple data items"""
        results = []
        for i, data in enumerate(data_list):
            result = self.verify_data_integrity(data)
            result["index"] = i
            results.append(result)
        
        success_count = sum(1 for r in results if r["matches_expected"])
        total_count = len(results)
        
        summary = {
            "total_items": total_count,
            "successful_verifications": success_count,
            "failed_verifications": total_count - success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
        
        return summary
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics for the integrity verification system"""
        return {
            "node_id": self.node_id,
            "blockchain_length": self.node.get_blockchain_length(),
            "pending_transactions": self.node.transaction_pool.qsize(),
            "monitored": self.monitoring,
            "total_integrity_records": len(self.verifier.verified_hashes),
            "latest_block": self.node.get_latest_block().index if self.node.blockchain else 0,
            "blockchain_valid": self.node.verify_blockchain(),
            "peers_connected": len(self.node.peers)
        }


# Decorator for automatic integrity recording
def integrity_protected(data_type: str = "function_output", 
                       metadata: Dict[str, Any] = None):
    """Decorator to automatically protect function output with integrity verification"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Get the integrity system from the instance (assuming it's available)
            instance = args[0] if args else None
            integrity_system = getattr(instance, 'integrity_system', None) if instance else None
            
            if integrity_system:
                # Record the function output with integrity protection
                try:
                    record_result = integrity_system.record_data_integrity(
                        result, 
                        data_type=f"{data_type}_{func.__name__}",
                        metadata={
                            "function": func.__name__,
                            "module": func.__module__,
                            "args": str(args[1:]) if len(args) > 1 else [],  # Exclude self
                            "kwargs": str(kwargs),
                            **(metadata or {})
                        }
                    )
                    
                    if record_result["success"]:
                        logger.info(f"Integrity protected output of {func.__name__}: {record_result['data_hash'][:16]}...")
                    else:
                        logger.warning(f"Failed to protect integrity of {func.__name__} output")
                        
                except Exception as e:
                    logger.error(f"Error recording integrity for {func.__name__}: {e}")
            
            return result
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    # Initialize blockchain integrity system
    integrity_system = BlockchainIntegritySystem(node_id="integrity_node_001")
    
    print("🔒 Blockchain-Based Integrity Verification System Initialized...")
    
    # Start monitoring
    integrity_system.start_monitoring()
    
    # Example: Record data integrity
    print("\nRecording data integrity...")
    sample_data = {
        "telemetry": {"temperature": 23.5, "pressure": 1013.25, "altitude": 500},
        "timestamp": datetime.utcnow().isoformat(),
        "source": "satellite_001"
    }
    
    record_result = integrity_system.record_data_integrity(
        sample_data, 
        data_type="telemetry_data",
        metadata={"mission": "mars_exploration", "version": "1.0"}
    )
    
    print(f"Data integrity recorded: {record_result}")
    
    # Example: Verify data integrity
    print("\nVerifying data integrity...")
    verify_result = integrity_system.verify_data_integrity(sample_data)
    print(f"Verification result: {verify_result}")
    
    # Example: Verify specific hash
    print("\nVerifying specific hash...")
    hash_check = integrity_system.verify_hash_exists(record_result["data_hash"])
    print(f"Hash verification: {hash_check}")
    
    # Example: Batch verification
    print("\nTesting batch verification...")
    batch_data = [
        {"sensor_id": "temp_001", "value": 25.0},
        {"sensor_id": "temp_002", "value": 24.5},
        {"sensor_id": "pres_001", "value": 1013.0}
    ]
    
    batch_result = integrity_system.batch_verify_integrity(batch_data)
    print(f"Batch verification: {batch_result['success_rate']:.2%} success rate")
    
    # Example: Add data with immediate verification
    print("\nAdding data with immediate verification...")
    config_data = {
        "system_config": {
            "max_temp": 80,
            "min_voltage": 11.5,
            "telemetry_interval": 30
        },
        "version": "2.1",
        "updated_by": "admin_user"
    }
    
    protected_result = integrity_system.add_data_with_verification(
        config_data,
        data_type="system_configuration",
        metadata={"change_type": "update", "approver": "security_officer"}
    )
    print(f"Protected result: {protected_result['success']}")
    
    # Get integrity report
    print("\nGenerating integrity report...")
    report = integrity_system.get_integrity_report()
    print(f"Integrity Report:")
    print(f"  - Total records: {report['total_integrity_records']}")
    print(f"  - Successful verifications: {report['successful_verifications']}")
    print(f"  - Failed verifications: {report['failed_verifications']}")
    print(f"  - Blockchain length: {report['blockchain_length']}")
    
    # Get verification history
    print("\nGetting verification history...")
    history = integrity_system.get_verification_history(limit=5)
    print(f"Recent verifications: {len(history)}")
    
    # Get system metrics
    print("\nGetting system metrics...")
    metrics = integrity_system.get_system_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Mine a block to process any pending transactions
    mined_block = integrity_system.node.mine_block()
    if mined_block:
        print(f"Mined block #{mined_block.index} with {len(mined_block.transactions)} transactions")
    
    # Verify blockchain integrity
    is_valid = integrity_system.node.verify_blockchain()
    print(f"Blockchain integrity: {'VALID' if is_valid else 'INVALID'}")
    
    # Stop monitoring
    integrity_system.stop_monitoring()
    
    print("\n✅ Blockchain Integrity Verification System Test Completed")