"""
Dashboard and Reporting Module
Real-time dashboards and reporting
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Dashboard:
    """Dashboard configuration"""
    name: str
    widgets: List[Dict]
    refresh_rate: int = 60


@dataclass
class Widget:
    """Dashboard widget"""
    widget_id: str
    widget_type: str  # chart, table, gauge, map, etc.
    title: str
    data_source: str
    config: Dict


class DashboardManager:
    """Manage dashboards"""
    
    def __init__(self):
        self.dashboards = {}
        self.data_sources = {}
    
    def create_dashboard(self, name: str) -> Dashboard:
        """Create dashboard"""
        dashboard = Dashboard(name=name, widgets=[])
        self.dashboards[name] = dashboard
        return dashboard
    
    def add_widget(self, dashboard: str, widget: Widget):
        """Add widget to dashboard"""
        if dashboard in self.dashboards:
            self.dashboards[dashboard].widgets.append({
                'id': widget.widget_id,
                'type': widget.widget_type,
                'title': widget.title,
                'data_source': widget.data_source,
                'config': widget.config
            })
    
    def get_dashboard(self, name: str) -> Dict:
        """Get dashboard config"""
        if name in self.dashboards:
            d = self.dashboards[name]
            return {
                'name': d.name,
                'widgets': d.widgets,
                'refresh_rate': d.refresh_rate
            }
        return {}
    
    def register_data_source(self, name: str, func):
        """Register data source"""
        self.data_sources[name] = func


class ReportGenerator:
    """Generate reports"""
    
    def __init__(self):
        self.templates = {}
    
    def add_template(self, name: str, template: Dict):
        """Add report template"""
        self.templates[name] = template
    
    def generate(self, template_name: str, data: Dict) -> Dict:
        """Generate report"""
        template = self.templates.get(template_name, {})
        
        report = {
            'title': template.get('title', 'Report'),
            'generated_at': datetime.now().isoformat(),
            'sections': []
        }
        
        for section in template.get('sections', []):
            section_data = self._process_section(section, data)
            report['sections'].append(section_data)
        
        return report
    
    def _process_section(self, section: Dict, data: Dict) -> Dict:
        """Process section"""
        section_type = section.get('type')
        
        if section_type == 'table':
            return {'type': 'table', 'data': data.get(section.get('data_key', []))}
        elif section_type == 'chart':
            return {'type': 'chart', 'chart_type': section.get('chart_type'), 'data': data.get(section.get('data_key', []))}
        elif section_type == 'summary':
            return {'type': 'summary', 'metrics': data.get(section.get('data_key', {}))}
        
        return section
    
    def export_json(self, report: Dict) -> str:
        """Export to JSON"""
        return json.dumps(report, indent=2)
    
    def export_html(self, report: Dict) -> str:
        """Export to HTML"""
        html = f"<html><head><title>{report.get('title', 'Report')}</title></head><body>"
        html += f"<h1>{report.get('title', 'Report')}</h1>"
        html += f"<p>Generated: {report.get('generated_at')}</p>"
        
        for section in report.get('sections', []):
            html += f"<div class='section'><h2>{section.get('type')}</h2>"
            html += f"<pre>{json.dumps(section.get('data', {}))}</pre></div>"
        
        html += "</body></html>"
        return html


class AlertManager:
    """Manage alerts"""
    
    def __init__(self):
        self.alerts = []
        self.handlers = []
    
    def add_alert(self, level: str, message: str, source: str = None):
        """Add alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'source': source,
            'acknowledged': False
        }
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.handlers:
            handler(alert)
    
    def get_alerts(self, level: str = None, acknowledged: bool = None) -> List[Dict]:
        """Get alerts"""
        filtered = self.alerts
        
        if level:
            filtered = [a for a in filtered if a['level'] == level]
        if acknowledged is not None:
            filtered = [a for a in filtered if a['acknowledged'] == acknowledged]
        
        return filtered
    
    def acknowledge(self, index: int):
        """Acknowledge alert"""
        if 0 <= index < len(self.alerts):
            self.alerts[index]['acknowledged'] = True
    
    def register_handler(self, handler):
        """Register alert handler"""
        self.handlers.append(handler)


class MetricsCollector:
    """Collect system metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, metric_name: str, value: float, tags: Dict = None):
        """Record metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            'timestamp': datetime.now().isoformat(),
            'value': value,
            'tags': tags or {}
        })
    
    def get_metrics(self, metric_name: str, window: int = 100) -> List[Dict]:
        """Get metrics"""
        return self.metrics.get(metric_name, [])[-window:]
    
    def get_statistics(self, metric_name: str) -> Dict:
        """Get statistics"""
        values = [m['value'] for m in self.get_metrics(metric_name)]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p50': np.percentile(values, 50),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99)
        }


# Example
if __name__ == "__main__":
    print("Testing Dashboard & Reporting...")
    
    # Dashboard
    dm = DashboardManager()
    dash = dm.create_dashboard("Telemetry")
    print(f"Dashboard: {dash.name}")
    
    # Report
    rg = ReportGenerator()
    rg.add_template("status", {
        'title': 'System Status',
        'sections': [
            {'type': 'summary', 'data_key': 'metrics'},
            {'type': 'table', 'data_key': 'events'}
        ]
    })
    report = rg.generate("status", {'metrics': {'cpu': 50, 'memory': 70}, 'events': []})
    print(f"Report: {report['title']}")
    
    # Alerts
    am = AlertManager()
    am.add_alert("warning", "High CPU usage", "monitor")
    alerts = am.get_alerts()
    print(f"Alerts: {len(alerts)}")
    
    # Metrics
    mc = MetricsCollector()
    mc.record("cpu", 50)
    mc.record("cpu", 60)
    stats = mc.get_statistics("cpu")
    print(f"CPU stats: mean={stats.get('mean', 0):.1f}%")