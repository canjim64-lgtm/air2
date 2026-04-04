"""
AirOne Data Management Integration
Combines AirOne backend with CKAN data models
"""
import os
import sys

# Add data_management to path
MODELS_PATH = os.path.join(os.path.dirname(__file__), 'data_management')
sys.path.insert(0, MODELS_PATH)

# Import CKAN models
from model import user, package, resource, group, tag, license, system, core
from dictization import model_dictize, model_save

__all__ = [
    'user',
    'package', 
    'resource',
    'group',
    'tag',
    'license',
    'system',
    'core',
    'model_dictize',
    'model_save',
]

class DataManager:
    """Unified data management for AirOne"""
    
    def __init__(self):
        self.models_path = MODELS_PATH
        self.initialized = False
    
    def init(self):
        """Initialize data models"""
        try:
            # Initialize CKAN model core
            core.init_model()
            self.initialized = True
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False
    
    def create_dataset(self, name, title, owner=None):
        """Create a new dataset/package"""
        if not self.initialized:
            self.init()
        
        from ckan.model.package import Package
        from ckan.model.meta import Session
        
        pkg = Package(name=name, title=title)
        if owner:
            pkg.owner_org = owner
        Session.add(pkg)
        Session.commit()
        return pkg
    
    def create_user(self, name, email, password):
        """Create a new user"""
        if not self.initialized:
            self.init()
        
        from ckan.model.user import User
        from ckan.model.meta import Session
        
        user = User(name=name, email=email)
        user.set_password(password)
        Session.add(user)
        Session.commit()
        return user
    
    def add_resource(self, dataset_id, name, url, format='csv'):
        """Add resource to dataset"""
        if not self.initialized:
            self.init()
        
        from ckan.model.resource import Resource
        from ckan.model.meta import Session
        
        res = Resource(
            package_id=dataset_id,
            name=name,
            url=url,
            format=format
        )
        Session.add(res)
        Session.commit()
        return res
    
    def serialize(self, obj):
        """Serialize model to dict"""
        from dictization.model_dictize import dictize
        return dictize(obj)
    
    def save(self, data, obj=None):
        """Save data to model"""
        from dictization.model_save import save
        return save(data, obj)


def get_manager():
    """Get DataManager instance"""
    return DataManager()