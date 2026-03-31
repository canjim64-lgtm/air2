"""
AirOne Professional v4.0 - Data Export Utilities
Export data in multiple formats
"""
# -*- coding: utf-8 -*-

import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """Export telemetry and analysis data in multiple formats"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.supported_formats = ['json', 'csv', 'txt', 'html', 'xml']
        
    def export(self, data: Dict[str, Any], format: str = 'json',
               filename: Optional[str] = None, **kwargs) -> str:
        """
        Export data to file
        
        Args:
            data: Data to export
            format: Export format (json, csv, txt, html, xml)
            filename: Output filename (auto-generated if None)
            **kwargs: Format-specific options
            
        Returns:
            Path to exported file
        """
        format = format.lower()
        
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.supported_formats}")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"airone_export_{timestamp}.{format}"
        
        filepath = self.output_dir / filename
        
        export_methods = {
            'json': self._export_json,
            'csv': self._export_csv,
            'txt': self._export_txt,
            'html': self._export_html,
            'xml': self._export_xml
        }
        
        export_methods[format](data, filepath, **kwargs)
        logger.info(f"Data exported to: {filepath}")
        
        return str(filepath)
    
    def _export_json(self, data: Dict[str, Any], filepath: Path, 
                     indent: int = 2, **kwargs):
        """Export as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
    
    def _export_csv(self, data: Dict[str, Any], filepath: Path, **kwargs):
        """Export as CSV"""
        # Handle telemetry data format
        if 'telemetry' in data:
            rows = data['telemetry']
        elif isinstance(data, list):
            rows = data
        else:
            rows = [data]
        
        if not rows:
            logger.warning("No data to export")
            return
        
        # Get all keys
        all_keys = set()
        for row in rows:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        
        all_keys = sorted(all_keys)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            
            for row in rows:
                if isinstance(row, dict):
                    writer.writerow({k: row.get(k, '') for k in all_keys})
    
    def _export_txt(self, data: Dict[str, Any], filepath: Path, **kwargs):
        """Export as formatted text"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("AirOne Professional v4.0 - Data Export\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            self._write_dict(f, data)
    
    def _write_dict(self, f, data: Any, indent: int = 0):
        """Recursively write dictionary to text file"""
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    f.write(f"{prefix}{key}:\n")
                    self._write_dict(f, value, indent + 1)
                elif isinstance(value, list):
                    f.write(f"{prefix}{key}:\n")
                    for item in value:
                        if isinstance(item, dict):
                            f.write(f"{prefix}  -\n")
                            self._write_dict(f, item, indent + 2)
                        else:
                            f.write(f"{prefix}  - {item}\n")
                else:
                    f.write(f"{prefix}{key}: {value}\n")
        elif isinstance(data, list):
            for item in data:
                f.write(f"{prefix}- {item}\n")
        else:
            f.write(f"{prefix}{data}\n")
    
    def _export_html(self, data: Dict[str, Any], filepath: Path, **kwargs):
        """Export as HTML report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AirOne Data Export</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #89b4fa;
            border-bottom: 2px solid #89b4fa;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #a6e3a1;
            margin-top: 30px;
        }}
        .metadata {{
            background: rgba(137, 180, 250, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(49, 50, 68, 0.5);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #45475a;
        }}
        th {{
            background: rgba(137, 180, 250, 0.2);
            color: #89b4fa;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background: rgba(137, 180, 250, 0.05);
        }}
        tr:hover {{
            background: rgba(137, 180, 250, 0.1);
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #45475a;
            color: #6c7086;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AirOne Professional v4.0</h1>
        <div class="metadata">
            <strong>Export Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Format:</strong> HTML Report<br>
            <strong>Records:</strong> {len(data.get('telemetry', [])) if isinstance(data, dict) else 'N/A'}
        </div>
"""
        
        # Add data sections
        if isinstance(data, dict):
            for section, content in data.items():
                html += f"        <h2>{section.replace('_', ' ').title()}</h2>\n"
                
                if isinstance(content, list) and content and isinstance(content[0], dict):
                    # Table for list of dicts
                    html += "        <table>\n            <thead>\n                <tr>\n"
                    for key in content[0].keys():
                        html += f"                    <th>{key.replace('_', ' ').title()}</th>\n"
                    html += "                </tr>\n            </thead>\n            <tbody>\n"
                    
                    for row in content[:100]:  # Limit to 100 rows
                        html += "                <tr>\n"
                        for value in row.values():
                            html += f"                    <td>{value}</td>\n"
                        html += "                </tr>\n"
                    
                    html += "            </tbody>\n        </table>\n"
                    
                    if len(content) > 100:
                        html += f"        <p><em>Showing 100 of {len(content)} records</em></p>\n"
                else:
                    html += f"        <p>{content}</p>\n"
        
        html += """
        <div class="footer">
            <p>AirOne Professional v4.0 - Ultimate Unified Edition</p>
            <p>© 2026 AirOne Development Team</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _export_xml(self, data: Dict[str, Any], filepath: Path, **kwargs):
        """Export as XML"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<airone_export>\n'
        xml += f'  <metadata>\n'
        xml += f'    <export_date>{datetime.now().isoformat()}</export_date>\n'
        xml += f'    <version>4.0</version>\n'
        xml += f'  </metadata>\n'
        
        xml += self._dict_to_xml(data, '  ')
        
        xml += '</airone_export>\n'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml)
    
    def _dict_to_xml(self, data: Any, indent: str = '') -> str:
        """Convert dictionary to XML string"""
        xml = ''
        
        if isinstance(data, dict):
            for key, value in data.items():
                key = key.replace(' ', '_').replace('-', '_')
                
                if isinstance(value, dict):
                    xml += f'{indent}<{key}>\n'
                    xml += self._dict_to_xml(value, indent + '  ')
                    xml += f'{indent}</{key}>\n'
                elif isinstance(value, list):
                    xml += f'{indent}<{key}>\n'
                    for item in value:
                        if isinstance(item, dict):
                            xml += self._dict_to_xml(item, indent + '  ')
                        else:
                            xml += f'{indent}  <item>{item}</item>\n'
                    xml += f'{indent}</{key}>\n'
                else:
                    xml += f'{indent}<{key}>{value}</{key}>\n'
        
        return xml
    
    def export_telemetry(self, telemetry_data: List[Dict[str, Any]], 
                         format: str = 'json',
                         filename: Optional[str] = None) -> str:
        """Export telemetry data"""
        data = {
            'metadata': {
                'type': 'telemetry',
                'export_date': datetime.now().isoformat(),
                'record_count': len(telemetry_data)
            },
            'telemetry': telemetry_data
        }
        
        return self.export(data, format, filename)
    
    def export_analysis(self, analysis_results: Dict[str, Any],
                       format: str = 'json',
                       filename: Optional[str] = None) -> str:
        """Export analysis results"""
        data = {
            'metadata': {
                'type': 'analysis',
                'export_date': datetime.now().isoformat()
            },
            'analysis': analysis_results
        }
        
        return self.export(data, format, filename)
    
    def export_report(self, report_data: Dict[str, Any],
                     format: str = 'html',
                     filename: Optional[str] = None) -> str:
        """Export comprehensive report"""
        data = {
            'metadata': {
                'type': 'report',
                'export_date': datetime.now().isoformat(),
                'version': '4.0'
            },
            **report_data
        }
        
        return self.export(data, format, filename)
    
    def list_exports(self) -> List[Path]:
        """List all exported files"""
        return sorted(self.output_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    def cleanup_old_exports(self, days: int = 30):
        """Remove exports older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for filepath in self.output_dir.glob('*'):
            if filepath.is_file() and filepath.stat().st_mtime < cutoff:
                filepath.unlink()
                logger.info(f"Deleted old export: {filepath}")


class BatchExporter:
    """Export multiple datasets at once"""
    
    def __init__(self, output_dir: str = "exports/batch"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.exporter = DataExporter(output_dir=str(self.output_dir))
        
    def export_batch(self, datasets: Dict[str, Dict[str, Any]], 
                     format: str = 'json') -> List[str]:
        """
        Export multiple datasets
        
        Args:
            datasets: Dict of {name: data}
            format: Export format
            
        Returns:
            List of exported file paths
        """
        exported_files = []
        
        for name, data in datasets.items():
            try:
                filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                filepath = self.exporter.export(data, format, filename)
                exported_files.append(filepath)
            except Exception as e:
                logger.error(f"Failed to export {name}: {e}")
        
        return exported_files
    
    def export_all_formats(self, data: Dict[str, Any], 
                          base_filename: str) -> Dict[str, str]:
        """
        Export same data in all formats
        
        Args:
            data: Data to export
            base_filename: Base filename (without extension)
            
        Returns:
            Dict of {format: filepath}
        """
        exported = {}
        
        for format in ['json', 'csv', 'txt', 'html']:
            try:
                filename = f"{base_filename}.{format}"
                filepath = self.exporter.export(data, format, filename)
                exported[format] = filepath
            except Exception as e:
                logger.error(f"Failed to export {format}: {e}")
        
        return exported


# Convenience functions
def export_data(data: Dict[str, Any], format: str = 'json', 
                filename: Optional[str] = None) -> str:
    """Quick export data"""
    return DataExporter().export(data, format, filename)


def export_telemetry(telemetry: List[Dict[str, Any]], 
                    format: str = 'json') -> str:
    """Quick export telemetry"""
    return DataExporter().export_telemetry(telemetry, format)


def export_to_json(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """Quick export to JSON"""
    return export_data(data, 'json', filename)


def export_to_csv(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """Quick export to CSV"""
    return export_data(data, 'csv', filename)


def export_to_html(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """Quick export to HTML"""
    return export_data(data, 'html', filename)


if __name__ == "__main__":
    # Test export
    test_data = {
        'telemetry': [
            {'timestamp': '2026-03-01T12:00:00', 'altitude': 100.5, 'velocity': 25.3},
            {'timestamp': '2026-03-01T12:00:01', 'altitude': 105.2, 'velocity': 26.1},
            {'timestamp': '2026-03-01T12:00:02', 'altitude': 110.8, 'velocity': 27.0}
        ],
        'system': {
            'cpu': 45.5,
            'memory': 62.3,
            'status': 'OK'
        }
    }
    
    exporter = DataExporter()
    
    print("Testing Data Export...")
    print()
    
    # Export in different formats
    for format in ['json', 'csv', 'txt', 'html']:
        filepath = exporter.export(test_data, format)
        print(f"[OK] Exported to {format}: {filepath}")
    
    print()
    print("All exports completed!")
