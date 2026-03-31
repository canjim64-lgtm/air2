"""
API Gateway Module
API gateway for microservices
"""

from typing import Dict, Any, Callable
import json


class APIRouter:
    """Route API requests"""
    
    def __init__(self):
        self.routes = {}
    
    def register(self, path: str, handler: Callable):
        """Register route"""
        self.routes[path] = handler
    
    def route(self, path: str, data: Dict) -> Any:
        """Route request"""
        if path in self.routes:
            return self.routes[path](data)
        return {"error": "Not found"}


class RateLimiter:
    """Rate limiting for API"""
    
    def __init__(self, limit: int = 100):
        self.limit = limit
        self.requests = {}
    
    def allow(self, client: str) -> bool:
        """Check if allowed"""
        count = self.requests.get(client, 0)
        if count >= self.limit:
            return False
        self.requests[client] = count + 1
        return True


class LoadBalancer:
    """Load balancer for services"""
    
    def __init__(self):
        self.services = []
        self.current = 0
    
    def add_service(self, url: str):
        """Add service"""
        self.services.append(url)
    
    def get_next(self) -> str:
        """Get next service"""
        if not self.services:
            return ""
        service = self.services[self.current]
        self.current = (self.current + 1) % len(self.services)
        return service


# Example
if __name__ == "__main__":
    router = APIRouter()
    router.register("/test", lambda d: {"result": "ok"})
    print(router.route("/test", {}))