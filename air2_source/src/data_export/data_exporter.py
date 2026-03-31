#!/usr/bin/env python3
"""
AirOne v4.0 - Data Export System
=================================

Export telemetry data to CSV, JSON, XML, PDF formats
"""

import os
import sys
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class DataExporter:
    """
    Data Export Manager
    
    Export telemetry data to multiple formats.
    """
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_csv(self, data: List[Dict], filename: str) -> str:
        """Export data to CSV"""
        if not data:
            return ""
            
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        return filepath
        
    def export_json(self, data: List[Dict], filename: str, pretty: bool = True) -> str:
        """Export data to JSON"""
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        with open(filepath, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)
                
        return filepath
        
    def export_xml(self, data: List[Dict], filename: str) -> str:
        """Export data to XML"""
        filepath = os.path.join(self.output_dir, f"{filename}.xml")
        
        root = ET.Element("telemetry_data")
        root.set("exported", datetime.now().isoformat())
        root.set("records", str(len(data)))
        
        for i, record in enumerate(data):
            item = ET.SubElement(root, "record")
            item.set("id", str(i))
            
            for key, value in record.items():
                child = ET.SubElement(item, key)
                child.text = str(value)
                
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        return filepath
        
    def export_text(self, data: List[Dict], filename: str) -> str:
        """Export data to plain text"""
        if not data:
            return ""
            
        filepath = os.path.join(self.output_dir, f"{filename}.txt")
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"AirOne Telemetry Export\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n")
            f.write(f"Records: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            keys = list(data[0].keys())
            f.write(" | ".join(keys) + "\n")
            f.write("-" * 80 + "\n")
            
            for record in data:
                values = [str(record.get(k, "")) for k in keys]
                f.write(" | ".join(values) + "\n")
                
        return filepath


def demo():
    """Demo export system"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║             AirOne v4.0 - Data Export System         ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    sample_data = [
        {"time": "10:00:00", "altitude": 500, "velocity": 25, "temperature": 22, "battery": 100},
        {"time": "10:00:05", "altitude": 520, "velocity": 27, "temperature": 21, "battery": 99},
        {"time": "10:00:10", "altitude": 550, "velocity": 30, "temperature": 20, "battery": 98},
    ]
    
    exporter = DataExporter()
    
    print("Exporting data...")
    csv_file = exporter.export_csv(sample_data, "telemetry")
    print(f"  ✓ CSV: {csv_file}")
    
    json_file = exporter.export_json(sample_data, "telemetry")
    print(f"  ✓ JSON: {json_file}")
    
    xml_file = exporter.export_xml(sample_data, "telemetry")
    print(f"  ✓ XML: {xml_file}")
    
    print("\n✓ Export complete!")


if __name__ == "__main__":
    demo()
