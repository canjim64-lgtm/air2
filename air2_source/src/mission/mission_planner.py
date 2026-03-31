#!/usr/bin/env python3
"""
AirOne v4.0 - Advanced Mission Planner
=======================================

Mission planning with waypoints, trajectories, and scheduling.
"""

import sys
import json
import time
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class Waypoint:
    """GPS Waypoint"""
    name: str
    latitude: float
    longitude: float
    altitude: float
    speed: float = 0.0
    duration: int = 0  # seconds to stay at waypoint
    
    def to_dict(self):
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "speed": self.speed,
            "duration": self.duration
        }


@dataclass
class FlightPhase:
    """Flight phase"""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    target_altitude: float = 0.0
    target_speed: float = 0.0
    waypoints: List[Waypoint] = field(default_factory=list)
    
    def duration_seconds(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return 0


class MissionPlanner:
    """
    Advanced Mission Planner
    
    Create, plan, and execute missions with waypoints and phases.
    """
    
    def __init__(self):
        self.missions = []
        self.current_mission = None
        self.waypoint_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, List[Waypoint]]:
        """Load waypoint templates"""
        return {
            "circular": [
                Waypoint("Center", 42.0, -75.0, 500, 20, 60),
                Waypoint("North", 42.01, -75.0, 500, 25, 30),
                Waypoint("East", 42.0, -74.99, 500, 25, 30),
                Waypoint("South", 41.99, -75.0, 500, 25, 30),
                Waypoint("West", 42.0, -75.01, 500, 25, 30),
            ],
            "figure8": [
                Waypoint("Start", 42.0, -75.0, 500, 20, 30),
                Waypoint("Loop1", 42.02, -75.0, 600, 30, 20),
                Waypoint("Cross", 42.0, -74.98, 500, 35, 10),
                Waypoint("Loop2", 41.98, -75.0, 600, 30, 20),
            ],
            "ascent": [
                Waypoint("Launch", 42.0, -75.0, 0, 0, 10),
                Waypoint("100m", 42.0, -75.0, 100, 15, 20),
                Waypoint("300m", 42.0, -75.0, 300, 20, 30),
                Waypoint("500m", 42.0, -75.0, 500, 25, 30),
                Waypoint("1000m", 42.0, -75.0, 1000, 30, 60),
            ],
            "descent": [
                Waypoint("1000m", 42.0, -75.0, 1000, 30, 30),
                Waypoint("500m", 42.0, -75.0, 500, 25, 30),
                Waypoint("300m", 42.0, -75.0, 300, 20, 30),
                Waypoint("100m", 42.0, -75.0, 100, 15, 20),
                Waypoint("Landing", 42.0, -75.0, 0, 5, 0),
            ],
            "search": [
                Waypoint("Search1", 42.01, -75.01, 400, 20, 15),
                Waypoint("Search2", 42.01, -74.99, 400, 20, 15),
                Waypoint("Search3", 41.99, -74.99, 400, 20, 15),
                Waypoint("Search4", 41.99, -75.01, 400, 20, 15),
            ]
        }
    
    def create_mission(self, name: str, mission_type: str = "custom") -> Dict[str, Any]:
        """Create a new mission"""
        
        mission = {
            "id": f"mission_{int(time.time())}",
            "name": name,
            "type": mission_type,
            "created": datetime.now().isoformat(),
            "status": "planned",
            "waypoints": [],
            "phases": [],
            "estimated_duration": 0,
            "total_distance": 0.0,
            "parameters": {
                "max_altitude": 1500,
                "max_speed": 50,
                "max_range": 5000,
                "battery_threshold": 20,
                "abort_altitude": 100
            }
        }
        
        # Add template waypoints if available
        if mission_type in self.waypoint_templates:
            mission["waypoints"] = [w.to_dict() for w in self.waypoint_templates[mission_type]]
            
        self.missions.append(mission)
        self.current_mission = mission
        
        return mission
    
    def add_waypoint(self, mission_id: str, waypoint: Waypoint) -> bool:
        """Add waypoint to mission"""
        
        for mission in self.missions:
            if mission["id"] == mission_id:
                mission["waypoints"].append(waypoint.to_dict())
                return True
        return False
    
    def calculate_metrics(self, mission_id: str) -> Dict[str, Any]:
        """Calculate mission metrics"""
        
        for mission in self.missions:
            if mission["id"] == mission_id:
                waypoints = mission["waypoints"]
                
                if not waypoints:
                    return {}
                
                # Calculate total distance
                total_distance = 0.0
                for i in range(len(waypoints) - 1):
                    w1 = waypoints[i]
                    w2 = waypoints[i + 1]
                    dist = self._haversine_distance(
                        w1["latitude"], w1["longitude"],
                        w2["latitude"], w2["longitude"]
                    )
                    total_distance += dist
                
                mission["total_distance"] = round(total_distance, 2)
                
                # Calculate estimated duration
                total_time = 0
                for wp in waypoints:
                    # Time to travel to waypoint (assume avg speed 20 m/s)
                    if wp.get("speed", 0) > 0:
                        total_time += wp.get("duration", 30)
                    else:
                        total_time += 30
                        
                mission["estimated_duration"] = total_time
                
                return {
                    "total_distance_m": round(total_distance, 2),
                    "total_distance_km": round(total_distance / 1000, 2),
                    "estimated_duration_sec": total_time,
                    "estimated_duration_min": round(total_time / 60, 1),
                    "waypoint_count": len(waypoints)
                }
                
        return {}
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate distance between two GPS points"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def validate_mission(self, mission_id: str) -> Dict[str, Any]:
        """Validate mission parameters"""
        
        for mission in self.missions:
            if mission["id"] == mission_id:
                errors = []
                warnings = []
                
                waypoints = mission["waypoints"]
                
                if not waypoints:
                    errors.append("No waypoints defined")
                
                # Check altitudes
                max_alt = mission["parameters"]["max_altitude"]
                for wp in waypoints:
                    if wp["altitude"] > max_alt:
                        errors.append(f"Waypoint {wp['name']} exceeds max altitude")
                    if wp["altitude"] < 0:
                        errors.append(f"Waypoint {wp['name']} has negative altitude")
                
                # Check speeds
                max_speed = mission["parameters"]["max_speed"]
                for wp in waypoints:
                    if wp.get("speed", 0) > max_speed:
                        warnings.append(f"Waypoint {wp['name']} exceeds max speed")
                
                # Check battery
                if mission["parameters"]["battery_threshold"] < 10:
                    warnings.append("Low battery threshold may cause early termination")
                
                return {
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings
                }
                
        return {"valid": False, "errors": ["Mission not found"]}
    
    def simulate_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """Simulate mission execution"""
        
        for mission in self.missions:
            if mission["id"] == mission_id:
                waypoints = mission["waypoints"]
                
                if not waypoints:
                    return []
                
                simulation = []
                current_time = datetime.now()
                
                for i, wp in enumerate(waypoints):
                    # Simulate travel to waypoint
                    steps = max(1, wp.get("duration", 30) // 5)
                    
                    for step in range(steps):
                        progress = (step + 1) / steps
                        
                        # Interpolate position
                        if i > 0:
                            prev = waypoints[i - 1]
                            lat = prev["latitude"] + (wp["latitude"] - prev["latitude"]) * progress
                            lon = prev["longitude"] + (wp["longitude"] - prev["longitude"]) * progress
                            alt = prev["altitude"] + (wp["altitude"] - prev["altitude"]) * progress
                        else:
                            lat = waypoints[0]["latitude"]
                            lon = waypoints[0]["longitude"]
                            alt = waypoints[0]["altitude"]
                        
                        simulation.append({
                            "timestamp": (current_time + timedelta(seconds=step * 5)).isoformat(),
                            "waypoint": wp["name"],
                            "latitude": round(lat, 6),
                            "longitude": round(lon, 6),
                            "altitude": round(alt, 1),
                            "speed": wp.get("speed", 20),
                            "progress": round(progress * 100, 1)
                        })
                    
                    current_time += timedelta(seconds=wp.get("duration", 30))
                
                return simulation
                
        return []
    
    def export_mission(self, mission_id: str, format: str = "json") -> str:
        """Export mission to file"""
        
        for mission in self.missions:
            if mission["id"] == mission_id:
                if format == "json":
                    return json.dumps(mission, indent=2)
                elif format == "csv":
                    # Export waypoints as CSV
                    lines = ["name,latitude,longitude,altitude,speed,duration"]
                    for wp in mission.get("waypoints", []):
                        lines.append(f"{wp['name']},{wp['latitude']},{wp['longitude']},{wp['altitude']},{wp.get('speed', 0)},{wp.get('duration', 0)}")
                    return "\n".join(lines)
                    
        return ""
    
    def list_missions(self) -> List[Dict[str, Any]]:
        """List all missions"""
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "type": m["type"],
                "status": m["status"],
                "waypoints": len(m.get("waypoints", []))
            }
            for m in self.missions
        ]


# CLI Interface
def main():
    """Mission Planner CLI"""
    
    planner = MissionPlanner()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              AirOne v4.0 - Mission Planner                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create sample missions
    print("Creating sample missions...\n")
    
    # Mission 1: Circular
    m1 = planner.create_mission("Circular Survey", "circular")
    metrics1 = planner.calculate_metrics(m1["id"])
    print(f"Mission: {m1['name']}")
    print(f"  Type: {m1['type']}")
    print(f"  Waypoints: {len(m1['waypoints'])}")
    print(f"  Distance: {metrics1.get('total_distance_km', 0)} km")
    print(f"  Duration: {metrics1.get('estimated_duration_min', 0)} min")
    print()
    
    # Mission 2: Figure 8
    m2 = planner.create_mission("Figure 8 Pattern", "figure8")
    metrics2 = planner.calculate_metrics(m2["id"])
    print(f"Mission: {m2['name']}")
    print(f"  Type: {m2['type']}")
    print(f"  Waypoints: {len(m2['waypoints'])}")
    print(f"  Distance: {metrics2.get('total_distance_km', 0)} km")
    print()
    
    # Mission 3: Ascent/Descent
    m3 = planner.create_mission("Vertical Profile", "ascent")
    metrics3 = planner.calculate_metrics(m3["id"])
    print(f"Mission: {m3['name']}")
    print(f"  Type: {m3['type']}")
    print(f"  Waypoints: {len(m3['waypoints'])}")
    print(f"  Max Altitude: {max([w['altitude'] for w in m3['waypoints']], default=0)} m")
    print()
    
    # Validate mission
    print("Validating missions...")
    validation = planner.validate_mission(m1["id"])
    print(f"  {m1['name']}: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
    if validation.get('warnings'):
        print(f"    Warnings: {', '.join(validation['warnings'])}")
    print()
    
    # Simulate mission
    print("Simulating mission...")
    sim = planner.simulate_mission(m1["id"])
    print(f"  Simulation steps: {len(sim)}")
    if sim:
        print(f"  First position: Lat {sim[0]['latitude']}, Lon {sim[0]['longitude']}, Alt {sim[0]['altitude']}m")
        print(f"  Final position:  Lat {sim[-1]['latitude']}, Lon {sim[-1]['longitude']}, Alt {sim[-1]['altitude']}m")
    print()
    
    # All missions
    print("All Missions:")
    for m in planner.list_missions():
        print(f"  - {m['name']} ({m['type']}) - {m['waypoints']} waypoints")
    
    print("\n" + "=" * 60)
    print("Mission Planner ready!")


if __name__ == "__main__":
    main()
