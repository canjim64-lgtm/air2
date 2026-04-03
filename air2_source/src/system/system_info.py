#!/usr/bin/env python3
"""
AirOne Professional v4.0 - System Information and Diagnostic Tool
Complete system diagnostics, information gathering, and health checks
"""

import sys
import platform
import os
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, List


class SystemInfo:
    """Gather comprehensive system information"""
    
    def __init__(self):
        self.info = {}
    
    def get_os_info(self) -> Dict[str, Any]:
        """Get operating system information"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation()
        }
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        try:
            import psutil
            
            # CPU info
            cpu_info = {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'cpu_freq_mhz': round(psutil.cpu_freq().current, 2) if psutil.cpu_freq() else 0,
                'cpu_usage_percent': psutil.cpu_percent(interval=1)
            }
            
            # Memory info
            mem_info = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(mem_info.total / (1024**3), 2),
                'available_gb': round(mem_info.available / (1024**3), 2),
                'used_percent': mem_info.percent
            }
            
            # Disk info
            disk_info = psutil.disk_usage('/')
            disk_info = {
                'total_gb': round(disk_info.total / (1024**3), 2),
                'used_gb': round(disk_info.used / (1024**3), 2),
                'free_gb': round(disk_info.free / (1024**3), 2),
                'used_percent': disk_info.percent
            }
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info
            }
        except:
            return {'error': 'Could not gather hardware info'}
    
    def get_python_packages(self) -> Dict[str, str]:
        """Get installed Python packages"""
        try:
            import pkg_resources
            packages = {}
            for pkg in pkg_resources.working_set:
                packages[pkg.project_name] = pkg.version
            return packages
        except:
            return {}
    
    def get_airone_info(self) -> Dict[str, Any]:
        """Get AirOne-specific information"""
        base_dir = Path(__file__).parent.parent.parent
        
        # Count source files
        src_dir = base_dir / 'src'
        py_files = list(src_dir.rglob('*.py')) if src_dir.exists() else []
        
        # Count modes
        modes_dir = src_dir / 'modes' if src_dir.exists() else None
        mode_files = list(modes_dir.glob('*_mode.py')) if modes_dir and modes_dir.exists() else []
        
        # Check directories
        directories = {
            'src': (src_dir / 'src').exists(),
            'config': (base_dir / 'config').exists(),
            'data': (base_dir / 'data').exists(),
            'logs': (base_dir / 'logs').exists(),
            'passwords': (base_dir / 'passwords').exists(),
            'models': (base_dir / 'models').exists()
        }
        
        return {
            'version': '4.0 Ultimate Unified Edition',
            'build_date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'source_files': len(py_files),
            'mode_files': len(mode_files),
            'directories': directories,
            'base_path': str(base_dir)
        }
    
    def get_all_info(self) -> Dict[str, Any]:
        """Get all system information"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'os': self.get_os_info(),
            'hardware': self.get_hardware_info(),
            'packages': self.get_python_packages(),
            'airone': self.get_airone_info()
        }


class DiagnosticTool:
    """System diagnostic and health check tool"""
    
    def __init__(self):
        self.diagnostics = {}
        self.errors = []
        self.warnings = []
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        current = sys.version_info[:2]
        required = (3, 8)
        if current >= required:
            return True
        else:
            self.errors.append(f"Python 3.8+ required, found {current[0]}.{current[1]}")
            return False
    
    def check_required_packages(self) -> List[str]:
        """Check required packages"""
        required = [
            'numpy', 'pandas', 'flask', 'cryptography',
            'PyQt5', 'torch', 'transformers', 'psutil'
        ]
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
                self.warnings.append(f"Missing package: {package}")
        
        return missing
    
    def check_directories(self) -> Dict[str, bool]:
        """Check required directories"""
        base_dir = Path(__file__).parent.parent.parent
        directories = {
            'src': base_dir / 'src',
            'config': base_dir / 'config',
            'data': base_dir / 'data',
            'logs': base_dir / 'logs',
            'passwords': base_dir / 'passwords'
        }
        
        results = {}
        for name, path in directories.items():
            exists = path.exists()
            results[name] = exists
            if not exists:
                self.warnings.append(f"Missing directory: {name}")
        
        return results
    
    def check_permissions(self) -> Dict[str, bool]:
        """Check file permissions"""
        base_dir = Path(__file__).parent.parent.parent
        test_file = base_dir / '.permission_test'
        
        results = {
            'read': False,
            'write': False,
            'execute': False
        }
        
        try:
            # Test read
            if base_dir.exists():
                results['read'] = True
            
            # Test write
            try:
                test_file.touch()
                results['write'] = True
                test_file.unlink()
            except Exception as e:
                results['write'] = False
                self.logger.debug(f"Write permission test failed: {e}")

            # Test execute
            results['execute'] = os.access(base_dir, os.X_OK)
            
        except Exception as e:
            self.errors.append(f"Permission check failed: {str(e)}")
        
        return results
    
    def check_network(self) -> Dict[str, Any]:
        """Check network connectivity"""
        import socket
        
        results = {
            'localhost': False,
            'dns': False,
            'internet': False
        }
        
        try:
            # Test localhost
            socket.gethostbyname('localhost')
            results['localhost'] = True
            
            # Test DNS
            socket.gethostbyname('www.google.com')
            results['dns'] = True
            
            # Test internet
            socket.create_connection(('www.google.com', 80), timeout=5)
            results['internet'] = True

        except Exception as e:
            results['internet'] = False
            self.logger.debug(f"Internet connectivity check failed: {e}")

        return results
    
    def run_all_diagnostics(self) -> Dict[str, Any]:
        """Run all diagnostic checks"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'python_version_ok': self.check_python_version(),
            'missing_packages': self.check_required_packages(),
            'directories': self.check_directories(),
            'permissions': self.check_permissions(),
            'network': self.check_network(),
            'errors': self.errors,
            'warnings': self.warnings,
            'health_score': self.calculate_health_score()
        }
    
    def calculate_health_score(self) -> int:
        """Calculate system health score (0-100)"""
        score = 100
        
        # Deduct for errors
        score -= len(self.errors) * 10
        
        # Deduct for warnings
        score -= len(self.warnings) * 5
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))


class ReportGenerator:
    """Generate system reports"""
    
    def __init__(self):
        self.report_dir = Path(__file__).parent.parent.parent / 'reports'
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_system_report(self) -> str:
        """Generate comprehensive system report"""
        info = SystemInfo()
        diagnostic = DiagnosticTool()
        
        report = {
            'report_type': 'System Information and Diagnostics',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'system_info': info.get_all_info(),
            'diagnostics': diagnostic.run_all_diagnostics(),
            'recommendations': self.generate_recommendations(diagnostic)
        }
        
        # Save report
        report_file = self.report_dir / f'system_report_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Also save as text
        text_file = self.report_dir / f'system_report_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.txt'
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(self.format_report_as_text(report))
        
        return str(report_file)
    
    def generate_recommendations(self, diagnostic: DiagnosticTool) -> List[str]:
        """Generate recommendations based on diagnostics"""
        recommendations = []
        
        if diagnostic.errors:
            recommendations.append("CRITICAL: Fix all errors before running AirOne")
        
        if diagnostic.warnings:
            recommendations.append("WARNING: Address warnings for optimal performance")
        
        if not diagnostic.check_python_version():
            recommendations.append("Upgrade Python to 3.8 or higher")
        
        missing = diagnostic.check_required_packages()
        if missing:
            recommendations.append(f"Install missing packages: pip install {' '.join(missing)}")
        
        perms = diagnostic.check_permissions()
        if not perms['write']:
            recommendations.append("Fix write permissions for application directory")
        
        network = diagnostic.check_network()
        if not network['internet']:
            recommendations.append("Check internet connection for package downloads")
        
        if not recommendations:
            recommendations.append("System is healthy - no issues detected")
        
        return recommendations
    
    def format_report_as_text(self, report: Dict) -> str:
        """Format report as readable text"""
        lines = []
        lines.append("="*80)
        lines.append("AirOne Professional v4.0 - System Report")
        lines.append("="*80)
        lines.append(f"Generated: {report['generated_at']}")
        lines.append("")
        
        # System Info
        lines.append("SYSTEM INFORMATION")
        lines.append("-"*80)
        os_info = report['system_info']['os']
        lines.append(f"OS: {os_info['system']} {os_info['release']}")
        lines.append(f"Python: {os_info['python_version']}")
        lines.append(f"Architecture: {os_info['architecture']}")
        lines.append("")
        
        # Hardware
        lines.append("HARDWARE")
        lines.append("-"*80)
        hw = report['system_info']['hardware']
        if 'cpu' in hw:
            lines.append(f"CPU: {hw['cpu'].get('physical_cores', '?')} cores")
            lines.append(f"Memory: {hw['memory'].get('total_gb', '?')} GB")
            lines.append(f"Disk: {hw['disk'].get('free_gb', '?')} GB free")
        lines.append("")
        
        # Diagnostics
        lines.append("DIAGNOSTICS")
        lines.append("-"*80)
        diag = report['diagnostics']
        lines.append(f"Health Score: {diag['health_score']}/100")
        lines.append(f"Errors: {len(diag['errors'])}")
        lines.append(f"Warnings: {len(diag['warnings'])}")
        lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-"*80)
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        lines.append("="*80)
        
        return '\n'.join(lines)


def run_system_check():
    """Run complete system check"""
    print("="*80)
    print("AirOne Professional v4.0 - System Information & Diagnostics")
    print("="*80)
    print()
    
    # Get system info
    print("Gathering system information...")
    info = SystemInfo()
    sys_info = info.get_all_info()
    
    print(f"✓ OS: {sys_info['os']['system']} {sys_info['os']['release']}")
    print(f"✓ Python: {sys_info['os']['python_version']}")
    print(f"✓ Source files: {sys_info['airone']['source_files']}")
    print(f"✓ Modes: {sys_info['airone']['mode_files']}")
    print()
    
    # Run diagnostics
    print("Running diagnostics...")
    diagnostic = DiagnosticTool()
    diag_results = diagnostic.run_all_diagnostics()
    
    print(f"✓ Health Score: {diag_results['health_score']}/100")
    print(f"✓ Errors: {len(diagnostic.errors)}")
    print(f"✓ Warnings: {len(diagnostic.warnings)}")
    print()
    
    # Generate report
    print("Generating report...")
    report_gen = ReportGenerator()
    report_file = report_gen.generate_system_report()
    
    print(f"✓ Report saved: {report_file}")
    print()
    
    # Show recommendations
    print("RECOMMENDATIONS:")
    print("-"*80)
    recommendations = report_gen.generate_recommendations(diagnostic)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print()
    
    print("="*80)
    print("System check complete!")
    print("="*80)
    
    return diag_results['health_score'] >= 80


if __name__ == '__main__':
    success = run_system_check()
    sys.exit(0 if success else 1)
