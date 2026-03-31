"""
REST API Module
REST API server
"""

from typing import Dict, Callable, Any
import json


class RESTAPI:
    """REST API server"""
    
    def __init__(self):
        self.endpoints = {}
    
    def route(self, path: str, methods: list = None):
        """Route decorator"""
        methods = methods or ["GET"]
        
        def decorator(func: Callable):
            self.endpoints[path] = {'func': func, 'methods': methods}
            return func
        return decorator
    
    def handle(self, path: str, method: str, data: Any = None) -> Dict:
        """Handle request"""
        if path in self.endpoints:
            endpoint = self.endpoints[path]
            if method in endpoint['methods']:
                return {'status': 200, 'data': endpoint['func'](data)}
            return {'status': 405, 'error': 'Method not allowed'}
        return {'status': 404, 'error': 'Not found'}
    
    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Start server"""
        print(f"REST API started on {host}:{port}")


# Example
if __name__ == "__main__":
    api = RESTAPI()
    @api.route("/data")
    def get_data(req):
        return {"value": 42}
    api.start()