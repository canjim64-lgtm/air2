"""
Swarm Coordination Module - Full Implementation
Multi-CanSat coordination and mesh networking
"""

import numpy as np
import time
from typing import Dict, List, Tuple
from collections import deque


class SwarmNode:
    """Individual CanSat in swarm"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.position = {'lat': 0, 'lon': 0, 'alt': 0}
        self.velocity = {'vx': 0, 'vy': 0, 'vz': 0}
        self.neighbors = []
        self.state = 'ACTIVE'
    
    def update_position(self, lat: float, lon: float, alt: float):
        self.position = {'lat': lat, 'lon': lon, 'alt': alt}
    
    def update_velocity(self, vx: float, vy: float, vz: float):
        self.velocity = {'vx': vx, 'vy': vy, 'vz': vz}


class SwarmManager:
    """Manage swarm of CanSats"""
    
    def __init__(self, max_nodes: int = 10):
        self.nodes = {}
        self.max_nodes = max_nodes
        self.formation = 'LINE'
    
    def add_node(self, node: SwarmNode):
        if len(self.nodes) < self.max_nodes:
            self.nodes[node.node_id] = node
    
    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def get_neighbors(self, node_id: str, max_distance: float = 1000) -> List[str]:
        if node_id not in self.nodes:
            return []
        
        node = self.nodes[node_id]
        neighbors = []
        
        for nid, other in self.nodes.items():
            if nid == node_id:
                continue
            
            dlat = node.position['lat'] - other.position['lat']
            dlon = node.position['lon'] - other.position['lon']
            distance = np.sqrt(dlat**2 + dlon**2) * 111000  # meters
            
            if distance < max_distance:
                neighbors.append(nid)
        
        return neighbors
    
    def set_formation(self, formation: str):
        self.formation = formation
    
    def compute_formation_positions(self, leader_pos: Dict) -> Dict:
        positions = {}
        
        if self.formation == 'LINE':
            for i, nid in enumerate(self.nodes):
                positions[nid] = {
                    'lat': leader_pos['lat'],
                    'lon': leader_pos['lon'] + i * 0.001,
                    'alt': leader_pos['alt']
                }
        
        elif self.formation == 'CIRCLE':
            n = len(self.nodes)
            for i, nid in enumerate(self.nodes):
                angle = 2 * np.pi * i / n
                positions[nid] = {
                    'lat': leader_pos['lat'] + 0.001 * np.cos(angle),
                    'lon': leader_pos['lon'] + 0.001 * np.sin(angle),
                    'alt': leader_pos['alt']
                }
        
        elif self.formation == 'V_SHAPE':
            for i, nid in enumerate(self.nodes):
                offset = (i % 5 - 2) * 0.001
                row = i // 5
                positions[nid] = {
                    'lat': leader_pos['lat'] - row * 0.001,
                    'lon': leader_pos['lon'] + offset,
                    'alt': leader_pos['alt']
                }
        
        return positions


class MeshNetwork:
    """Mesh networking for swarm"""
    
    def __init__(self):
        self.routing_table = {}
        self.packet_queue = deque(maxlen=1000)
    
    def build_route(self, source: str, destination: str, 
                   neighbors: Dict[str, List[str]]) -> List[str]:
        if source == destination:
            return [source]
        
        visited = {source}
        queue = [(source, [source])]
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in neighbors.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    
                    if neighbor == destination:
                        return new_path
                    
                    queue.append((neighbor, new_path))
        
        return []
    
    def forward_packet(self, packet: Dict, route: List[str]) -> bool:
        self.packet_queue.append(packet)
        return True


class FormationController:
    """Control swarm formation"""
    
    def __init__(self):
        self.target_offsets = {}
    
    def compute_control(self, node: SwarmNode, 
                       target: Dict, neighbors: List[SwarmNode]) -> Dict:
        # Formation keeping
        avg_neighbor_pos = {'lat': 0, 'lon': 0, 'alt': 0}
        if neighbors:
            for n in neighbors:
                avg_neighbor_pos['lat'] += n.position['lat']
                avg_neighbor_pos['lon'] += n.position['lon']
                avg_neighbor_pos['alt'] += n.position['alt']
            avg_neighbor_pos['lat'] /= len(neighbors)
            avg_neighbor_pos['lon'] /= len(neighbors)
            avg_neighbor_pos['alt'] /= len(neighbors)
        
        # Error from target
        dlat = target['lat'] - node.position['lat']
        dlon = target['lon'] - node.position['lon']
        dalt = target['alt'] - node.position['alt']
        
        # Error from neighbors
        nlat = avg_neighbor_pos['lat'] - node.position['lat']
        nlon = avg_neighbor_pos['lon'] - node.position['lon']
        
        # Combined control
        k_target = 1.0
        k_neighbor = 0.5
        
        roll = np.clip((k_target * dlon + k_neighbor * nlon) * 1000, -45, 45)
        pitch = np.clip((k_target * dalt + k_neighbor * (avg_neighbor_pos['alt'] - node.position['alt'])) * 10, -30, 30)
        
        return {'pitch': pitch, 'roll': roll, 'throttle': 50}


if __name__ == "__main__":
    sm = SwarmManager()
    node = SwarmNode("NODE1")
    sm.add_node(node)
    print(f"Nodes: {len(sm.nodes)}")