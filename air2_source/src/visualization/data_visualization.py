#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Data Visualization System
Complete data visualization with charts, graphs, dashboards, and real-time updates
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


class DataVisualizer:
    """Advanced data visualization system"""
    
    def __init__(self):
        self.charts = []
        self.dashboards = []
        self.visualization_dir = Path(__file__).parent.parent / 'visualizations'
        self.visualization_dir.mkdir(parents=True, exist_ok=True)
    
    def create_line_chart(self, title: str, data: List[Dict], x_key: str = 'x', y_key: str = 'y',
                         width: int = 800, height: int = 600) -> str:
        """Create a line chart"""
        chart_id = f"line_chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart {{ margin: 20px auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div id="chart" class="chart"></div>
    <script>
        var data = [{
            'x': {[d[x_key] for d in data]},
            'y': {[d[y_key] for d in data]},
            'type': 'scatter',
            'mode': 'lines+markers'
        }];
        var layout = {{
            title: '{title}',
            xaxis: {{ title: '{x_key}' }},
            yaxis: {{ title: '{y_key}' }},
            width: {width},
            height: {height}
        }};
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        
        chart_file = self.visualization_dir / f'{chart_id}.html'
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.charts.append({
            'id': chart_id,
            'type': 'line_chart',
            'title': title,
            'file': str(chart_file),
            'created_at': datetime.utcnow().isoformat()
        })
        
        return str(chart_file)
    
    def create_bar_chart(self, title: str, categories: List[str], values: List[float],
                        width: int = 800, height: int = 600) -> str:
        """Create a bar chart"""
        chart_id = f"bar_chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart {{ margin: 20px auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div id="chart" class="chart"></div>
    <script>
        var data = [{
            'x': {categories},
            'y': {values},
            'type': 'bar'
        }];
        var layout = {{
            title: '{title}',
            width: {width},
            height: {height}
        }};
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        
        chart_file = self.visualization_dir / f'{chart_id}.html'
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.charts.append({
            'id': chart_id,
            'type': 'bar_chart',
            'title': title,
            'file': str(chart_file),
            'created_at': datetime.utcnow().isoformat()
        })
        
        return str(chart_file)
    
    def create_pie_chart(self, title: str, labels: List[str], values: List[float],
                        width: int = 800, height: int = 600) -> str:
        """Create a pie chart"""
        chart_id = f"pie_chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart {{ margin: 20px auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div id="chart" class="chart"></div>
    <script>
        var data = [{
            'labels': {labels},
            'values': {values},
            'type': 'pie'
        }];
        var layout = {{
            title: '{title}',
            width: {width},
            height: {height}
        }};
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        
        chart_file = self.visualization_dir / f'{chart_id}.html'
        with open(chart_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.charts.append({
            'id': chart_id,
            'type': 'pie_chart',
            'title': title,
            'file': str(chart_file),
            'created_at': datetime.utcnow().isoformat()
        })
        
        return str(chart_file)
    
    def create_dashboard(self, title: str, charts: List[str], layout: str = 'grid') -> str:
        """Create a dashboard with multiple charts"""
        dashboard_id = f"dashboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        chart_links = '\n'.join([
            f'<iframe src="{chart}" width="100%" height="600" frameborder="0"></iframe>'
            for chart in charts
        ])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #667eea; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .chart {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated: {datetime.utcnow().isoformat()}</p>
    </div>
    <div class="charts">
        {chart_links}
    </div>
</body>
</html>
"""
        
        dashboard_file = self.visualization_dir / f'{dashboard_id}.html'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.dashboards.append({
            'id': dashboard_id,
            'title': title,
            'charts': charts,
            'file': str(dashboard_file),
            'created_at': datetime.utcnow().isoformat()
        })
        
        return str(dashboard_file)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get visualization statistics"""
        return {
            'total_charts': len(self.charts),
            'total_dashboards': len(self.dashboards),
            'charts_by_type': self._count_charts_by_type(),
            'storage_directory': str(self.visualization_dir)
        }
    
    def _count_charts_by_type(self) -> Dict[str, int]:
        """Count charts by type"""
        types = {}
        for chart in self.charts:
            chart_type = chart['type']
            types[chart_type] = types.get(chart_type, 0) + 1
        return types


def create_visualizer() -> DataVisualizer:
    """Create and return data visualizer"""
    return DataVisualizer()


if __name__ == '__main__':
    # Test visualization system
    logging.basicConfig(level=logging.INFO)
    
    visualizer = create_visualizer()
    
    # Create line chart
    data = [{'x': i, 'y': i * 2} for i in range(10)]
    line_chart = visualizer.create_line_chart('Test Line Chart', data)
    print(f"Line chart created: {line_chart}")
    
    # Create bar chart
    bar_chart = visualizer.create_bar_chart('Test Bar Chart', ['A', 'B', 'C'], [10, 20, 30])
    print(f"Bar chart created: {bar_chart}")
    
    # Create pie chart
    pie_chart = visualizer.create_pie_chart('Test Pie Chart', ['X', 'Y', 'Z'], [40, 35, 25])
    print(f"Pie chart created: {pie_chart}")
    
    # Create dashboard
    dashboard = visualizer.create_dashboard('Test Dashboard', [line_chart, bar_chart, pie_chart])
    print(f"Dashboard created: {dashboard}")
    
    # Get statistics
    stats = visualizer.get_statistics()
    print(f"Visualization statistics: {stats}")
    
    print("Visualization system tests completed")
