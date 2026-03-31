"""
AirOne Professional v4.0 - Automated Test Suite
Comprehensive testing for all system components
"""
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestResult:
    """Test result container"""
    
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now().isoformat()
    
    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        return f"{status} {self.name}: {self.message} ({self.duration:.3f}s)"


class TestSuite:
    """Automated test suite for AirOne Professional"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
    def run_test(self, name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test"""
        start = time.time()
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start
            
            if result[0]:
                test_result = TestResult(name, True, result[1], duration)
            else:
                test_result = TestResult(name, False, result[1], duration)
        except Exception as e:
            duration = time.time() - start
            test_result = TestResult(name, False, f"Exception: {str(e)}", duration)
        
        self.results.append(test_result)
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        self.start_time = datetime.now()
        
        print("="*70)
        print("  AirOne Professional v4.0 - Automated Test Suite")
        print("="*70)
        print()
        
        # Module import tests
        print("[1/6] Running Module Import Tests...")
        self.test_module_imports()
        
        # Configuration tests
        print("[2/6] Running Configuration Tests...")
        self.test_configurations()
        
        # Data export tests
        print("[3/6] Running Data Export Tests...")
        self.test_data_export()
        
        # Error handling tests
        print("[4/6] Running Error Handling Tests...")
        self.test_error_handling()
        
        # Utility tests
        print("[5/6] Running Utility Tests...")
        self.test_utilities()
        
        # Integration tests
        print("[6/6] Running Integration Tests...")
        self.test_integration()
        
        self.end_time = datetime.now()
        
        # Print summary
        self.print_summary()
        
        return self.get_report()
    
    def test_module_imports(self):
        """Test module imports"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        sys.path.insert(0, str(Path(__file__).parent))
        
        modules_to_test = [
            ("error_handler", lambda: __import__("error_handler", fromlist=["ErrorHandler"])),
            ("startup_diagnostics", lambda: __import__("startup_diagnostics", fromlist=["StartupDiagnostics"])),
            ("update_checker", lambda: __import__("update_checker", fromlist=["UpdateChecker"])),
            ("data_export", lambda: __import__("data_export", fromlist=["DataExporter"])),
            ("web_dashboard", lambda: __import__("web_dashboard", fromlist=["start_dashboard"])),
        ]
        
        for name, import_func in modules_to_test:
            self.run_test(f"Import {name}", lambda f=import_func: (True, "Module loaded") if f() else (False, "Failed"))
    
    def test_configurations(self):
        """Test configuration files"""
        # Test launch_config.json
        def test_launch_config():
            config_path = Path("launch_config.json")
            if not config_path.exists():
                return (False, "File not found")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'launch_config' in config and 'default_settings' in config:
                return (True, "Valid configuration")
            return (False, "Missing required sections")
        
        self.run_test("launch_config.json", test_launch_config)
        
        # Test directory structure
        def test_directories():
            required_dirs = ['logs', 'data', 'config', 'passwords', 'src']
            missing = [d for d in required_dirs if not Path(d).exists()]
            
            if missing:
                return (False, f"Missing: {', '.join(missing)}")
            return (True, "All directories present")
        
        self.run_test("Directory structure", test_directories)
    
    def test_data_export(self):
        """Test data export functionality"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from data_export import DataExporter
        
        test_data = {
            'test': 'data',
            'values': [1, 2, 3],
            'timestamp': datetime.now().isoformat()
        }
        
        def test_json_export():
            exporter = DataExporter(output_dir="exports/test")
            filepath = exporter.export(test_data, 'json', 'test.json')
            exists = Path(filepath).exists()
            if exists:
                Path(filepath).unlink()  # Cleanup
            return (exists, "JSON export" if exists else "Export failed")
        
        self.run_test("JSON Export", test_json_export)
        
        def test_csv_export():
            exporter = DataExporter(output_dir="exports/test")
            filepath = exporter.export({'data': [{'a': 1, 'b': 2}]}, 'csv', 'test.csv')
            exists = Path(filepath).exists()
            if exists:
                Path(filepath).unlink()
            return (exists, "CSV export" if exists else "Export failed")
        
        self.run_test("CSV Export", test_csv_export)
        
        def test_html_export():
            exporter = DataExporter(output_dir="exports/test")
            filepath = exporter.export(test_data, 'html', 'test.html')
            exists = Path(filepath).exists()
            if exists:
                Path(filepath).unlink()
            return (exists, "HTML export" if exists else "Export failed")
        
        self.run_test("HTML Export", test_html_export)
    
    def test_error_handling(self):
        """Test error handling"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from error_handler import ErrorHandler, handle_exceptions
        
        def test_error_handler_creation():
            handler = ErrorHandler()
            return (handler is not None, "Handler created")
        
        self.run_test("Error Handler Creation", test_error_handler_creation)
        
        @handle_exceptions(default_return={"error": "handled"}, retry_count=0)
        def test_function():
            raise ValueError("Test error")
        
        def test_exception_handling():
            result = test_function()
            return (result.get("error") == "handled", "Exception handled")
        
        self.run_test("Exception Handling", test_exception_handling)
    
    def test_utilities(self):
        """Test utility functions"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from update_checker import get_version, UpdateChecker
        
        def test_version():
            version = get_version()
            return (version == "4.0.0", f"Version: {version}")
        
        self.run_test("Version Check", test_version)
        
        def test_update_checker():
            checker = UpdateChecker()
            status = checker.get_update_status()
            return ('current_version' in status, "Update checker working")
        
        self.run_test("Update Checker", test_update_checker)
        
        from startup_diagnostics import StartupDiagnostics
        
        def test_diagnostics():
            diag = StartupDiagnostics()
            return (diag is not None, "Diagnostics initialized")
        
        self.run_test("Diagnostics Init", test_diagnostics)
    
    def test_integration(self):
        """Test integration between components"""
        def test_full_workflow():
            # Test complete workflow
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from data_export import DataExporter
            from update_checker import get_version
            
            version = get_version()
            exporter = DataExporter()
            
            # Create test report
            report = {
                'version': version,
                'test_time': datetime.now().isoformat(),
                'status': 'OK'
            }
            
            filepath = exporter.export(report, 'json', 'integration_test.json')
            exists = Path(filepath).exists()
            
            if exists:
                Path(filepath).unlink()
            
            return (exists and version == "4.0.0", "Integration test passed")
        
        self.run_test("Full Workflow", test_full_workflow)
    
    def print_summary(self):
        """Print test summary"""
        print()
        print("="*70)
        print("  TEST SUMMARY")
        print("="*70)
        print()
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total = len(self.results)
        
        for result in self.results:
            print(f"  {result}")
        
        print()
        print("-"*70)
        print(f"  Total Tests:  {total}")
        print(f"  Passed:       {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed:       {failed} ({failed/total*100:.1f}%)")
        print(f"  Duration:     {(self.end_time - self.start_time).total_seconds():.2f}s")
        print("="*70)
        
        if failed == 0:
            print("\n  [SUCCESS] All tests passed!")
        else:
            print(f"\n  [WARNING] {failed} test(s) failed")
    
    def get_report(self) -> Dict[str, Any]:
        """Get test report"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        return {
            'test_date': self.start_time.isoformat() if self.start_time else None,
            'end_date': self.end_time.isoformat() if self.end_time else None,
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total * 100 if total > 0 else 0,
            'results': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'duration': r.duration,
                    'timestamp': r.timestamp
                }
                for r in self.results
            ]
        }
    
    def save_report(self, filepath: str = "logs/test_report.json"):
        """Save test report to file"""
        report = self.get_report()
        
        Path(filepath).parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Test report saved to: {filepath}")


def run_tests():
    """Run all tests"""
    suite = TestSuite()
    report = suite.run_all_tests()
    suite.save_report()
    
    return report['passed'] == report['total_tests']


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
