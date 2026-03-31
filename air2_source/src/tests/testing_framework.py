"""
Testing Module
Testing utilities
"""

import unittest
from typing import Any


class TestCase:
    """Base test case"""
    
    def assertEqual(self, a: Any, b: Any):
        """Assert equal"""
        assert a == b, f"{a} != {b}"
    
    def assertTrue(self, a: Any):
        """Assert true"""
        assert a, "Expected True"
    
    def assertFalse(self, a: Any):
        """Assert false"""
        assert not a, "Expected False"


class TestSuite:
    """Test suite"""
    
    def __init__(self):
        self.tests = []
    
    def add_test(self, test_case: str, test_func: callable):
        """Add test"""
        self.tests.append({'case': test_case, 'func': test_func})
    
    def run(self):
        """Run tests"""
        passed = 0
        for test in self.tests:
            try:
                test['func']()
                passed += 1
            except Exception as e:
                print(f"FAILED: {test['case']}: {e}")
        print(f"Passed: {passed}/{len(self.tests)}")


# Example
if __name__ == "__main__":
    suite = TestSuite()
    suite.add_test("test1", lambda: 1 + 1 == 2)
    suite.run()