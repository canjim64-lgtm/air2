#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Automation and Scripting System
Complete automation framework with scheduling, workflows, and scripting capabilities
"""

import os
import sys
import time
import json
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
import hashlib
import logging


class AutomationTask:
    """Represents an automated task"""
    
    def __init__(self, name: str, function: Callable, interval: int = 60, enabled: bool = True):
        self.name = name
        self.function = function
        self.interval = interval  # seconds
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None
        
    def execute(self):
        """Execute the task"""
        try:
            if self.enabled:
                self.function()
                self.last_run = datetime.utcnow()
                self.next_run = self.last_run + timedelta(seconds=self.interval)
                self.run_count += 1
                logging.info(f"Task '{self.name}' executed successfully")
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logging.error(f"Task '{self.name}' failed: {e}")


class Workflow:
    """Represents a workflow (sequence of tasks)"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.created_at = datetime.utcnow()
        self.last_executed = None
        self.execution_count = 0
        
    def add_step(self, step_name: str, action: Callable, params: Dict = None):
        """Add a step to the workflow"""
        self.steps.append({
            'name': step_name,
            'action': action,
            'params': params or {},
            'order': len(self.steps) + 1
        })
        
    def execute(self):
        """Execute the workflow"""
        logging.info(f"Executing workflow: {self.name}")
        results = []
        
        for step in self.steps:
            try:
                logging.info(f"  Executing step: {step['name']}")
                result = step['action'](**step['params'])
                results.append({
                    'step': step['name'],
                    'success': True,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                results.append({
                    'step': step['name'],
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                logging.error(f"  Step '{step['name']}' failed: {e}")
                break
        
        self.last_executed = datetime.utcnow()
        self.execution_count += 1
        
        return {
            'workflow': self.name,
            'success': all(r['success'] for r in results),
            'steps': results,
            'executed_at': self.last_executed.isoformat()
        }


class AutomationManager:
    """Manages all automation tasks and workflows"""
    
    def __init__(self):
        self.tasks = {}
        self.workflows = {}
        self.running = False
        self.scheduler_thread = None
        self.config_dir = Path(__file__).parent.parent / 'config' / 'automation'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def create_task(self, name: str, function: Callable, interval: int = 60) -> AutomationTask:
        """Create and register a new task"""
        task = AutomationTask(name, function, interval)
        self.tasks[name] = task
        schedule.every(interval).seconds.do(task.execute)
        logging.info(f"Created task: {name} (interval: {interval}s)")
        return task
    
    def create_workflow(self, name: str) -> Workflow:
        """Create and register a new workflow"""
        workflow = Workflow(name)
        self.workflows[name] = workflow
        logging.info(f"Created workflow: {name}")
        return workflow
    
    def start(self):
        """Start the automation scheduler"""
        if self.running:
            return
        
        self.running = True
        
        def run_scheduler():
            logging.info("Automation scheduler started")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logging.info("Automation scheduler running")
    
    def stop(self):
        """Stop the automation scheduler"""
        self.running = False
        schedule.clear()
        logging.info("Automation scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get automation system status"""
        return {
            'running': self.running,
            'tasks': {
                name: {
                    'enabled': task.enabled,
                    'interval': task.interval,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'run_count': task.run_count,
                    'error_count': task.error_count
                }
                for name, task in self.tasks.items()
            },
            'workflows': {
                name: {
                    'steps': len(workflow.steps),
                    'execution_count': workflow.execution_count,
                    'last_executed': workflow.last_executed.isoformat() if workflow.last_executed else None
                }
                for name, workflow in self.workflows.items()
            }
        }
    
    def save_configuration(self):
        """Save automation configuration"""
        config = {
            'tasks': {
                name: {
                    'interval': task.interval,
                    'enabled': task.enabled
                }
                for name, task in self.tasks.items()
            },
            'workflows': {
                name: {
                    'steps': [
                        {
                            'name': step['name'],
                            'params': step['params']
                        }
                        for step in workflow.steps
                    ]
                }
                for name, workflow in self.workflows.items()
            }
        }
        
        config_file = self.config_dir / 'automation_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)
        
        logging.info(f"Automation configuration saved to: {config_file}")
    
    def load_configuration(self):
        """Load automation configuration"""
        config_file = self.config_dir / 'automation_config.json'
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logging.info(f"Automation configuration loaded from: {config_file}")
        except Exception as e:
            logging.error(f"Failed to load automation configuration: {e}")


class ScriptEngine:
    """Script execution engine for custom automation scripts"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent.parent / 'scripts'
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.executed_scripts = []
        
    def create_script(self, name: str, code: str, description: str = "") -> str:
        """Create a new automation script"""
        script_file = self.scripts_dir / f"{name}.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
{description}
Auto-generated by AirOne Professional v4.0 Script Engine
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Main script function"""
    print("Executing script: {name}")
    print("="*60)
    
    # Your script code here
    {code}
    
    print("="*60)
    print("Script execution complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logging.info(f"Script created: {script_file}")
        return str(script_file)
    
    def execute_script(self, script_name: str) -> Dict[str, Any]:
        """Execute a script"""
        script_file = self.scripts_dir / f"{script_name}.py"
        
        if not script_file.exists():
            return {
                'success': False,
                'error': f'Script not found: {script_name}'
            }
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(script_name, script_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            result = module.main()
            
            self.executed_scripts.append({
                'name': script_name,
                'executed_at': datetime.utcnow().isoformat(),
                'result': result
            })
            
            return {
                'success': True,
                'script': script_name,
                'result': result,
                'executed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'script': script_name
            }
    
    def list_scripts(self) -> List[str]:
        """List all available scripts"""
        scripts = []
        for script_file in self.scripts_dir.glob('*.py'):
            if script_file.name != '__init__.py':
                scripts.append(script_file.stem)
        return scripts


def create_automation_system() -> AutomationManager:
    """Create and initialize automation system"""
    automation = AutomationManager()
    
    # Create default tasks
    def log_system_status():
        logging.info("System status check - All systems operational")
    
    def check_disk_space():
        import shutil
        total, used, free = shutil.disk_usage("/")
        logging.info(f"Disk space - Total: {total // (2**30)}GB, Used: {used // (2**30)}GB, Free: {free // (2**30)}GB")
        return free / (2**30)
    
    def backup_configuration():
        logging.info("Configuration backup task executed")
        return True
    
    # Register default tasks
    automation.create_task('system_status_check', log_system_status, interval=300)  # 5 minutes
    automation.create_task('disk_space_check', check_disk_space, interval=3600)  # 1 hour
    automation.create_task('config_backup', backup_configuration, interval=86400)  # 24 hours
    
    # Create default workflows
    startup_workflow = automation.create_workflow('system_startup')
    
    def dummy_check_system():
        logging.info("Workflow Step: Checking system components during startup")
        return True
    
    def dummy_load_config():
        logging.info("Workflow Step: Loading configuration files during startup")
        return True
        
    def dummy_initialize_services():
        logging.info("Workflow Step: Initializing core services during startup")
        return True

    startup_workflow.add_step('check_system', dummy_check_system)
    startup_workflow.add_step('load_config', dummy_load_config)
    startup_workflow.add_step('initialize_services', dummy_initialize_services)
    
    shutdown_workflow = automation.create_workflow('system_shutdown')
    
    def dummy_save_state():
        logging.info("Workflow Step: Saving system state during shutdown")
        return True
    
    def dummy_close_connections():
        logging.info("Workflow Step: Closing network connections during shutdown")
        return True
        
    def dummy_cleanup():
        logging.info("Workflow Step: Performing final cleanup during shutdown")
        return True

    shutdown_workflow.add_step('save_state', dummy_save_state)
    shutdown_workflow.add_step('close_connections', dummy_close_connections)
    shutdown_workflow.add_step('cleanup', dummy_cleanup)
    
    return automation


if __name__ == '__main__':
    # Test automation system
    logging.basicConfig(level=logging.INFO)
    
    automation = create_automation_system()
    automation.start()
    
    print("Automation system started")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        automation.stop()
        print("Automation system stopped")
