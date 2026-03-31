"""
Mission Planning Module
Mission planning and scheduling
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Waypoint:
    lat: float
    lon: float
    alt: float
    action: str


class MissionPlanner:
    """Plan missions"""
    
    def __init__(self):
        self.waypoints = []
    
    def add_waypoint(self, lat: float, lon: float, alt: float, action: str = "waypoint"):
        """Add waypoint"""
        self.waypoints.append(Waypoint(lat, lon, alt, action))
    
    def calculate_route(self) -> Dict:
        """Calculate route"""
        total_distance = 0
        for i in range(len(self.waypoints) - 1):
            p1 = self.waypoints[i]
            p2 = self.waypoints[i+1]
            total_distance += self._distance(p1.lat, p1.lon, p2.lat, p2.lon)
        
        return {
            'waypoints': len(self.waypoints),
            'total_distance': total_distance,
            'estimated_time': total_distance / 50  # Assume 50 m/s
        }
    
    def _distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance"""
        return np.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111000


# Example
if __name__ == "__main__":
    planner = MissionPlanner()
    planner.add_waypoint(34.0, -118.0, 100, "start")
    planner.add_waypoint(34.1, -118.1, 200, "end")
    print(f"Route: {planner.calculate_route()}")