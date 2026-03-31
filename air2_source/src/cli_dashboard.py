"""
AirOne Professional v4.0 - CLI Dashboard
Terminal-based real-time dashboard with rich UI
"""
# -*- coding: utf-8 -*-

import sys
import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, Any, List

# Try to import rich library for better terminal UI
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Installing basic console mode...")
    from rich.console import Console

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CLIDashboard:
    """Terminal-based dashboard for real-time monitoring"""
    
    def __init__(self, refresh_rate: float = 1.0):
        self.refresh_rate = refresh_rate
        self.running = False
        self.console = Console()
        self.data = {
            'telemetry': {},
            'system': {},
            'mission': {}
        }
        
    def start(self):
        """Start the dashboard"""
        self.running = True
        
        if not RICH_AVAILABLE:
            self._run_basic_mode()
        else:
            self._run_rich_mode()
    
    def _run_rich_mode(self):
        """Run with rich library for advanced UI"""
        from rich.live import Live
        from rich.layout import Layout
        from rich.panel import Panel
        
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split(
            Layout(name="telemetry"),
            Layout(name="system")
        )
        
        layout["right"].update(
            Panel(self._create_mission_table(), title="Mission Status")
        )
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while self.running:
                self._update_data()
                layout["header"].update(self._create_header())
                layout["telemetry"].update(
                    Panel(self._create_telemetry_table(), title="Telemetry")
                )
                layout["system"].update(
                    Panel(self._create_system_table(), title="System")
                )
                layout["footer"].update(self._create_footer())
                time.sleep(self.refresh_rate)
    
    def _run_basic_mode(self):
        """Run in basic mode without rich live updates"""
        try:
            while self.running:
                self.console.clear()
                self._update_data()
                
                # Print header
                self.console.print(
                    Panel(
                        "[bold cyan]AirOne Professional v4.0 - CLI Dashboard[/bold cyan]",
                        subtitle=f"[yellow]{datetime.now().strftime('%H:%M:%S')}[/yellow]"
                    )
                )
                
                # Print telemetry
                self.console.print("\n[bold green]Telemetry:[/bold green]")
                table = self._create_telemetry_table()
                self.console.print(table)
                
                # Print system
                self.console.print("\n[bold blue]System:[/bold blue]")
                sys_table = self._create_system_table()
                self.console.print(sys_table)
                
                # Print footer
                self.console.print(
                    "\n[yellow]Press Ctrl+C to exit[/yellow]"
                )
                
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self.running = False
    
    def _update_data(self):
        """Update dashboard data"""
        # Simulate telemetry data
        self.data['telemetry'] = {
            'altitude': round(random.uniform(100, 500), 1),
            'velocity': round(random.uniform(10, 30), 1),
            'temperature': round(random.uniform(20, 30), 1),
            'pressure': round(random.uniform(1010, 1015), 1),
            'battery': round(random.uniform(80, 100), 1),
            'signal': random.randint(-70, -40)
        }
        
        # Simulate system data
        self.data['system'] = {
            'cpu': round(random.uniform(20, 60), 1),
            'memory': round(random.uniform(40, 70), 1),
            'disk': round(random.uniform(40, 50), 1),
            'uptime': time.time() % 86400
        }
        
        # Simulate mission data
        self.data['mission'] = {
            'state': random.choice(['IDLE', 'ACTIVE', 'PAUSED']),
            'progress': round(random.uniform(0, 100), 1),
            'events': random.randint(0, 10)
        }
    
    def _create_header(self) -> Panel:
        """Create header panel"""
        from rich.text import Text
        
        text = Text()
        text.append("🚀 AirOne Professional v4.0", style="bold cyan")
        text.append(" | ", style="dim")
        text.append("CLI Dashboard", style="green")
        
        return Panel(
            text,
            subtitle=f"[yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]"
        )
    
    def _create_telemetry_table(self) -> Table:
        """Create telemetry table"""
        if not RICH_AVAILABLE:
            from rich.table import Table
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Unit", style="yellow")
        
        tel = self.data.get('telemetry', {})
        
        table.add_row("Altitude", f"{tel.get('altitude', 0):.1f}", "m")
        table.add_row("Velocity", f"{tel.get('velocity', 0):.1f}", "m/s")
        table.add_row("Temperature", f"{tel.get('temperature', 0):.1f}", "°C")
        table.add_row("Pressure", f"{tel.get('pressure', 0):.1f}", "hPa")
        table.add_row("Battery", f"{tel.get('battery', 0):.1f}", "%")
        table.add_row("Signal", f"{tel.get('signal', 0)}", "dBm")
        
        return table
    
    def _create_system_table(self) -> Table:
        """Create system table"""
        if not RICH_AVAILABLE:
            from rich.table import Table
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="green")
        table.add_column("Status", style="yellow")
        
        sys = self.data.get('system', {})
        
        cpu = sys.get('cpu', 0)
        mem = sys.get('memory', 0)
        disk = sys.get('disk', 0)
        
        table.add_row(
            "CPU",
            f"{cpu:.1f}%",
            "[green]OK[/green]" if cpu < 80 else "[red]HIGH[/red]"
        )
        table.add_row(
            "Memory",
            f"{mem:.1f}%",
            "[green]OK[/green]" if mem < 80 else "[red]HIGH[/red]"
        )
        table.add_row(
            "Disk",
            f"{disk:.1f}%",
            "[green]OK[/green]" if disk < 80 else "[red]HIGH[/red]"
        )
        
        uptime = sys.get('uptime', 0)
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        table.add_row("Uptime", f"{hours}h {minutes}m", "[green]Stable[/green]")
        
        return table
    
    def _create_mission_table(self) -> Table:
        """Create mission status table"""
        if not RICH_AVAILABLE:
            from rich.table import Table
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="cyan")
        table.add_column("Status", style="green")
        
        mission = self.data.get('mission', {})
        
        state = mission.get('state', 'IDLE')
        progress = mission.get('progress', 0)
        events = mission.get('events', 0)
        
        table.add_row("State", f"[cyan]{state}[/cyan]")
        table.add_row("Progress", f"{progress:.1f}%")
        table.add_row("Events", f"{events}")
        
        return table
    
    def _create_footer(self) -> Panel:
        """Create footer panel"""
        from rich.text import Text
        
        text = Text()
        text.append("Status: ", style="dim")
        text.append("● Online", style="green")
        text.append(" | ", style="dim")
        text.append("Refresh: ", style="dim")
        text.append(f"{self.refresh_rate}s", style="yellow")
        
        return Panel(text)
    
    def stop(self):
        """Stop the dashboard"""
        self.running = False


def run_dashboard(refresh_rate: float = 1.0):
    """Quick function to run dashboard"""
    dashboard = CLIDashboard(refresh_rate)
    try:
        dashboard.start()
    except KeyboardInterrupt:
        dashboard.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AirOne CLI Dashboard')
    parser.add_argument('--refresh', type=float, default=1.0, help='Refresh rate in seconds')
    args = parser.parse_args()
    
    print("="*70)
    print("  AirOne Professional v4.0 - CLI Dashboard")
    print("="*70)
    print()
    print("Starting dashboard...")
    print("Press Ctrl+C to exit")
    print()
    
    run_dashboard(args.refresh)
