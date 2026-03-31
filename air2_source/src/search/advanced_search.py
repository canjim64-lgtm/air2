#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Search and Indexing System
Full-text search with indexing, filters, and advanced query capabilities
"""

import os
import sys
import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import logging
import re
from collections import defaultdict
import pickle


class SearchIndex:
    """Inverted index for full-text search"""
    
    def __init__(self):
        self.index = defaultdict(set)  # word -> set of document IDs
        self.documents = {}  # doc_id -> document data
        self.metadata = {}  # doc_id -> metadata
        self.lock = threading.RLock()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z0-9_]+\b', text)
        return words
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None):
        """Add document to index"""
        with self.lock:
            # Tokenize content
            words = self.tokenize(content)
            
            # Add to index
            for word in words:
                self.index[word].add(doc_id)
            
            # Store document
            self.documents[doc_id] = content
            self.metadata[doc_id] = metadata or {}
    
    def remove_document(self, doc_id: str):
        """Remove document from index"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            # Remove from index
            content = self.documents[doc_id]
            words = self.tokenize(content)
            for word in words:
                if doc_id in self.index[word]:
                    self.index[word].remove(doc_id)
            
            # Remove document
            del self.documents[doc_id]
            if doc_id in self.metadata:
                del self.metadata[doc_id]
            
            return True
    
    def search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search for documents"""
        with self.lock:
            # Tokenize query
            query_words = self.tokenize(query)
            
            if not query_words:
                return []
            
            # Find matching documents
            result_sets = [self.index.get(word, set()) for word in query_words]
            
            # Intersection of all word sets (AND search)
            if result_sets:
                matching_docs = result_sets[0]
                for result_set in result_sets[1:]:
                    matching_docs = matching_docs.intersection(result_set)
            else:
                matching_docs = set()
            
            # Apply filters
            if filters:
                filtered_docs = set()
                for doc_id in matching_docs:
                    doc_metadata = self.metadata.get(doc_id, {})
                    match = True
                    for key, value in filters.items():
                        if doc_metadata.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_docs.add(doc_id)
                matching_docs = filtered_docs
            
            # Return results
            results = []
            for doc_id in matching_docs:
                results.append({
                    'id': doc_id,
                    'content': self.documents[doc_id][:200] + '...' if len(self.documents[doc_id]) > 200 else self.documents[doc_id],
                    'metadata': self.metadata.get(doc_id, {}),
                    'relevance': len(query_words)  # Simple relevance scoring
                })
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        with self.lock:
            return {
                'documents': len(self.documents),
                'unique_words': len(self.index),
                'total_words': sum(len(docs) for docs in self.index.values())
            }


class SearchEngine:
    """Advanced search engine with multiple indexes"""
    
    def __init__(self):
        self.indexes = {}  # index_name -> SearchIndex
        self.lock = threading.RLock()
        self.index_dir = Path(__file__).parent.parent / 'data' / 'search'
        self.index_dir.mkdir(parents=True, exist_ok=True)
    
    def create_index(self, name: str) -> SearchIndex:
        """Create a new search index"""
        with self.lock:
            index = SearchIndex()
            self.indexes[name] = index
            return index
    
    def get_index(self, name: str) -> Optional[SearchIndex]:
        """Get search index by name"""
        return self.indexes.get(name)
    
    def search_all(self, query: str, indexes: List[str] = None) -> Dict[str, List[Dict]]:
        """Search across multiple indexes"""
        results = {}
        
        if indexes is None:
            indexes = list(self.indexes.keys())
        
        for index_name in indexes:
            index = self.indexes.get(index_name)
            if index:
                results[index_name] = index.search(query)
        
        return results
    
    def save_indexes(self):
        """Save indexes to disk"""
        with self.lock:
            for name, index in self.indexes.items():
                index_file = self.index_dir / f'{name}.index'
                with open(index_file, 'wb') as f:
                    pickle.dump({
                        'index': dict(index.index),
                        'documents': index.documents,
                        'metadata': index.metadata
                    }, f)
    
    def load_indexes(self):
        """Load indexes from disk"""
        with self.lock:
            for index_file in self.index_dir.glob('*.index'):
                name = index_file.stem
                try:
                    with open(index_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    index = SearchIndex()
                    index.index = defaultdict(set, data['index'])
                    index.documents = data['documents']
                    index.metadata = data['metadata']
                    self.indexes[name] = index
                except Exception as e:
                    logging.error(f"Failed to load index {name}: {e}")


class QueryBuilder:
    """Advanced query builder for complex searches"""
    
    def __init__(self):
        self.query_parts = []
        self.filters = {}
        self.order_by = None
        self.order_direction = 'ASC'
        self.limit = None
        self.offset = None
    
    def search(self, *terms: str) -> 'QueryBuilder':
        """Add search terms"""
        self.query_parts.extend(terms)
        return self
    
    def filter(self, key: str, value: Any) -> 'QueryBuilder':
        """Add filter"""
        self.filters[key] = value
        return self
    
    def order_by_field(self, field: str, direction: str = 'ASC') -> 'QueryBuilder':
        """Set order by"""
        self.order_by = field
        self.order_direction = direction.upper()
        return self
    
    def set_limit(self, limit: int) -> 'QueryBuilder':
        """Set result limit"""
        self.limit = limit
        return self
    
    def set_offset(self, offset: int) -> 'QueryBuilder':
        """Set result offset"""
        self.offset = offset
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build query"""
        return {
            'query': ' '.join(self.query_parts),
            'filters': self.filters,
            'order_by': self.order_by,
            'order_direction': self.order_direction,
            'limit': self.limit,
            'offset': self.offset
        }


def create_search_engine() -> SearchEngine:
    """Create and return search engine"""
    engine = SearchEngine()
    engine.load_indexes()
    return engine


if __name__ == '__main__':
    # Test search system
    logging.basicConfig(level=logging.INFO)
    
    engine = create_search_engine()
    
    # Create test index
    index = engine.create_index('documents')
    
    # Add test documents
    index.add_document('doc1', 'AirOne Professional is a complete CanSat ground station solution with AI integration', {'type': 'manual', 'category': 'documentation'})
    index.add_document('doc2', 'The web server mode provides real-time telemetry visualization', {'type': 'manual', 'category': 'features'})
    index.add_document('doc3', 'Password rotation system ensures maximum security with 256-character passwords', {'type': 'manual', 'category': 'security'})
    
    # Search
    results = index.search('AirOne security')
    print(f"Search results: {len(results)}")
    for result in results:
        print(f"  - {result['id']}: {result['content'][:100]}")
    
    # Search with filters
    results = index.search('manual', filters={'category': 'security'})
    print(f"Filtered results: {len(results)}")
    
    # Get stats
    stats = index.get_stats()
    print(f"Index stats: {stats}")
    
    # Test query builder
    query = QueryBuilder()
    query.search('AirOne', 'security')
    query.filter('type', 'manual')
    query.set_limit(10)
    built_query = query.build()
    print(f"Built query: {built_query}")
    
    # Save indexes
    engine.save_indexes()
    print("Search system tests completed")
