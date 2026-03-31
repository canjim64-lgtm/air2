"""
Autonomous Swarm Meshing (ASM) for AirOne Professional v4.0
Calculates optimal communication routes through a dynamic satellite swarm mesh using link-cost graph theory.
"""
import logging
import heapq
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)

class SwarmMeshRouter:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ASM")
        self.nodes = set()
        self.links: Dict[str, List[Tuple[str, float]]] = {} # Node -> list of (Neighbor, RSSI_Cost)
        self.logger.info("Autonomous Swarm Meshing (ASM) Router Initialized.")

    def update_link(self, node_a: str, node_b: str, rssi: float):
        """Updates or adds a directional link between nodes. rssi is used as inverse cost."""
        self.nodes.add(node_a)
        self.nodes.add(node_b)
        
        # Link cost: Lower RSSI (closer to 0) means lower cost.
        # Scale: -100dBm -> 100 cost, -40dBm -> 40 cost.
        cost = abs(rssi)
        
        if node_a not in self.links: self.links[node_a] = []
        # Update existing link or add new
        self.links[node_a] = [(n, c) for n, c in self.links[node_a] if n != node_b]
        self.links[node_a].append((node_b, cost))

    def calculate_path(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """Dijkstra's algorithm to find the lowest-latency path through the swarm mesh."""
        if start_node not in self.nodes or end_node not in self.nodes:
            return {"status": "ERROR", "message": "Node not found"}

        queue = [(0, start_node, [])]
        seen = set()
        
        while queue:
            (cost, current, path) = heapq.heappop(queue)
            if current in seen: continue
            
            path = path + [current]
            if current == end_node:
                return {
                    "status": "PATH_FOUND",
                    "path": path,
                    "total_link_cost": round(cost, 2),
                    "hop_count": len(path) - 1
                }
            
            seen.add(current)
            for neighbor, link_cost in self.links.get(current, []):
                heapq.heappush(queue, (cost + link_cost, neighbor, path))

        return {"status": "NO_PATH", "message": "No routing possible through mesh"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asm = SwarmMeshRouter()
    asm.update_link("SAT-1", "SAT-2", -50)
    asm.update_link("SAT-2", "SAT-3", -60)
    asm.update_link("SAT-1", "SAT-3", -115) # Very weak link
    print(asm.calculate_path("SAT-1", "SAT-3")) # Should route via SAT-2
