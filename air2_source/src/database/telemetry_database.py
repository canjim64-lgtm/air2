"""
Database Module
Database operations and management
"""

import sqlite3
from typing import Dict, List, Any


class Database:
    """Database interface"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def create_table(self, name: str, columns: Dict[str, str]):
        """Create table"""
        cols = ", ".join([f"{k} {v}" for k, v in columns.items()])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")
        self.conn.commit()
    
    def insert(self, table: str, data: Dict):
        """Insert data"""
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        self.cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", 
                          list(data.values()))
        self.conn.commit()
    
    def select(self, table: str, where: str = "", limit: int = 100) -> List[Dict]:
        """Select data"""
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        query += f" LIMIT {limit}"
        
        self.cursor.execute(query)
        cols = [d[0] for d in self.cursor.description]
        return [dict(zip(cols, row)) for row in self.cursor.fetchall()]
    
    def close(self):
        """Close database"""
        self.conn.close()


# Example
if __name__ == "__main__":
    db = Database()
    db.create_table("telemetry", {"id": "INTEGER PRIMARY KEY", "data": "TEXT"})
    db.insert("telemetry", {"data": "test"})
    print(db.select("telemetry"))