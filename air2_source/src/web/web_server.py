"""
Web Server Module
Lightweight web server
"""

from typing import Dict, Callable


class WebServer:
    """Simple web server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.routes = {}
    
    def route(self, path: str):
        """Route decorator"""
        def decorator(func: Callable):
            self.routes[path] = func
            return func
        return decorator
    
    def handle(self, path: str, params: Dict = None) -> str:
        """Handle request"""
        if path in self.routes:
            return self.routes[path](params or {})
        return "404 Not Found"
    
    def start(self):
        """Start server"""
        print(f"Server started on {self.host}:{self.port}")


# Example
if __name__ == "__main__":
    server = WebServer()
    @server.route("/test")
    def test(req):
        return "Hello"
    server.start()