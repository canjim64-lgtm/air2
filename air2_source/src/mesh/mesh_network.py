"""
Mesh Networking Module - Full Implementation
Ad-hoc mesh networking
"""

import numpy as np


class MeshNetwork:
    """Ad-hoc mesh networking"""
    
    def __init__(self):
        self.nodes = {}
        self.routing_table = {}
    
    def add_node(self, node_id: str, position: dict):
        self.nodes[node_id] = {'position': position, 'neighbors': []}
    
    def discover_neighbors(self, max_range: float = 1000):
        for id1, n1 in self.nodes.items():
            for id2, n2 in self.nodes.items():
                if id1 != id2:
                    d = self._distance(n1['position'], n2['position'])
                    if d < max_range:
                        n1['neighbors'].append(id2)
    
    def _distance(self, p1: dict, p2: dict) -> float:
        dlat = p1.get('lat', 0) - p2.get('lat', 0)
        dlon = p1.get('lon', 0) - p2.get('lon', 0)
        return np.sqrt(dlat**2 + dlon**2) * 111000
    
    def find_route(self, src: str, dst: str) -> list:
        if src not in self.nodes or dst not in self.nodes:
            return []
        
        visited = {src}
        queue = [(src, [src])]
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self.nodes[current]['neighbors']:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    
                    if neighbor == dst:
                        return new_path
                    
                    queue.append((neighbor, new_path))
        
        return []


class MeshProtocol:
    """Mesh protocol implementation"""
    
    def __init__(self):
        self.packet_id = 0
    
    def create_packet(self, src: str, dst: str, data: dict) -> dict:
        self.packet_id += 1
        return {
            'id': self.packet_id,
            'src': src,
            'dst': dst,
            'data': data,
            'hops': 0,
            'ttl': 10
        }


if __name__ == "__main__":
    mesh = MeshNetwork()
    mesh.add_node('A', {'lat': 51.5, 'lon': -0.1})
    mesh.add_node('B', {'lat': 51.51, 'lon': -0.09})
    mesh.discover_neighbors()
    print(f"Neighbors A: {mesh.nodes['A']['neighbors']}")