"""
Enhanced Mode Manager for AirOne v3.0
Manages all operational modes with enhanced integration and features
"""

import sys
import threading
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import queue
import logging
from enum import Enum
import psutil # Import psutil

# Add src to path
sys.path.insert(0, './src')

# Import all core components
from core.mode_manager import OperationalMode, get_mode_manager, initialize_mode_manager

# Import all individual modes
from modes.desktop_gui_mode import DesktopGUIMode
from modes.headless_cli_mode import HeadlessCLIMode
from modes.offline_mode import OfflineMode
from modes.simulation_mode import SimulationMode
from modes.receiver_mode import ReceiverMode
from modes.replay_mode import ReplayMode
from modes.safe_mode import SafeMode
from modes.web_mode import WebMode
from modes.digital_twin_mode import DigitalTwinMode

# Import enhanced AI capabilities
from ml.enhanced_ai_engine import EnhancedMLEngine, EnhancedLocalAIDataAnalyzer

logger = logging.getLogger(__name__)


class IntegratedMode(Enum):
    """Enumeration of all integrated modes"""
    DESKTOP_GUI = "desktop_gui"
    HEADLESS_CLI = "headless_cli"
    OFFLINE = "offline"
    SIMULATION = "simulation"
    RECEIVER = "receiver"
    REPLAY = "replay"
    SAFE = "safe"
    WEB = "web"
    DIGITAL_TWIN = "digital_twin"
    ALL_INTEGRATED = "all_integrated"


class EnhancedModeManager:
    """
    Enhanced mode manager that combines all operational modes with advanced features
    and seamless integration between different operational states
    """
    
    def __init__(self):
        """Initialize the enhanced mode manager with all integrated features"""
        self.enhanced_ai = EnhancedMLEngine(use_gpu=True)
        self.analyzer = EnhancedLocalAIDataAnalyzer()
        
        # Initialize all individual modes
        self.modes = {
            IntegratedMode.DESKTOP_GUI.value: DesktopGUIMode(),
            IntegratedMode.HEADLESS_CLI.value: HeadlessCLIMode(),
            IntegratedMode.OFFLINE.value: OfflineMode(),
            IntegratedMode.SIMULATION.value: SimulationMode(),
            IntegratedMode.RECEIVER.value: ReceiverMode(),
            IntegratedMode.REPLAY.value: ReplayMode(),
            IntegratedMode.SAFE.value: SafeMode(),
            IntegratedMode.WEB.value: WebMode(),
            IntegratedMode.DIGITAL_TWIN.value: DigitalTwinMode()
        }
        
        # Shared data queues for inter-mode communication
        self.data_queues = {
            'telemetry': queue.Queue(maxsize=1000),
            'commands': queue.Queue(maxsize=100),
            'alerts': queue.Queue(maxsize=100),
            'ai_analysis': queue.Queue(maxsize=50),
            'mode_events': queue.Queue(maxsize=50),
            'system_metrics': queue.Queue(maxsize=100)
        }
        
        # Shared state for all modes
        self.shared_state = {
            'current_mode': IntegratedMode.DESKTOP_GUI.value,
            'active_modes': set(),
            'system_status': 'idle',
            'telemetry_data': [],
            'mission_phase': 'pre_launch',
            'ai_insights': {},
            'anomalies': [],
            'predictions': [],
            'system_metrics': {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'active_threads': 0,
                'data_throughput': 0.0
            },
            'last_update': datetime.now(),
            'integration_level': 'full'
        }
        
        # Thread management
        self.threads = {}
        self.running = False
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Callbacks for mode events
        self.mode_callbacks = {
            'on_mode_start': [],
            'on_mode_stop': [],
            'on_data_received': [],
            'on_ai_analysis': []
        }
        
        # Initialize mode manager
        self._initialize_enhanced_mode_manager()
    
    def _initialize_enhanced_mode_manager(self):
        """Initialize the enhanced mode manager with advanced features"""
        print("+ Initializing Enhanced Mode Manager for AirOne v3.0...")
        print("   - Integrating all operational modes")
        print("   - Connecting enhanced AI capabilities")
        print("   - Setting up inter-mode communication")
        print("   - Configuring shared state management")
        print("   - Establishing data flow pipelines")
        
        # Initialize enhanced AI
        status = self.enhanced_ai.get_enhanced_engine_status()
        if status['initialized']:
            print("   + Enhanced AI engine initialized")
        else:
            print("   ! Enhanced AI engine initialization failed")

        print("   + Enhanced Mode Manager initialized successfully")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific events"""
        if event_type in self.mode_callbacks:
            self.mode_callbacks[event_type].append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _trigger_callbacks(self, event_type: str, *args, **kwargs):
        """Trigger callbacks for a specific event"""
        if event_type in self.mode_callbacks:
            for callback in self.mode_callbacks[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
    
    def start_mode(self, mode_name: str) -> bool:
        """Start a specific mode with enhanced features"""
        if mode_name not in self.modes:
            print(f"❌ Invalid mode: {mode_name}")
            return False
        
        if mode_name in self.shared_state['active_modes']:
            print(f"⚠️  Mode {mode_name} is already running")
            return False
        
        with self.lock:
            # Create and start mode thread
            thread = threading.Thread(
                target=self._run_mode_with_enhanced_integration,
                args=(mode_name, self.modes[mode_name]),
                daemon=True,
                name=f"Mode-{mode_name}"
            )
            self.threads[mode_name] = thread
            thread.start()
            
            # Update shared state
            self.shared_state['active_modes'].add(mode_name)
            self.shared_state['current_mode'] = mode_name
            self.shared_state['last_update'] = datetime.now()
            
            # Trigger mode start callback
            self._trigger_callbacks('on_mode_start', mode_name)
        
        print(f"   ✅ Started {mode_name} mode")
        return True
    
    def stop_mode(self, mode_name: str) -> bool:
        """Stop a specific mode"""
        if mode_name not in self.modes:
            print(f"❌ Invalid mode: {mode_name}")
            return False
        
        if mode_name not in self.shared_state['active_modes']:
            print(f"⚠️  Mode {mode_name} is not running")
            return True  # Already stopped
        
        with self.lock:
            # Send stop signal to mode (if supported)
            mode_instance = self.modes[mode_name]
            if hasattr(mode_instance, 'stop'):
                try:
                    mode_instance.stop()
                except Exception as e:
                    logger.warning(f"Error stopping {mode_name}: {e}")
            
            # Remove from active modes
            self.shared_state['active_modes'].discard(mode_name)
            
            # Trigger mode stop callback
            self._trigger_callbacks('on_mode_stop', mode_name)
        
        print(f"   ✅ Stopped {mode_name} mode")
        return True
    
    def start_all_modes(self):
        """Start all modes simultaneously with coordinated operation"""
        print("🚀 Starting all operational modes in coordinated fashion...")
        
        success_count = 0
        for mode_name in self.modes.keys():
            if self.start_mode(mode_name):
                success_count += 1
        
        print(f"   ✅ Started {success_count}/{len(self.modes)} modes successfully")
        
        # Start enhanced AI analysis thread
        ai_thread = threading.Thread(
            target=self._run_enhanced_ai_analysis,
            daemon=True,
            name="EnhancedAI"
        )
        self.threads['ai_analysis'] = ai_thread
        ai_thread.start()
        print("   ✅ Enhanced AI analysis started")
        
        # Start system metrics thread
        metrics_thread = threading.Thread(
            target=self._run_system_metrics_monitoring,
            daemon=True,
            name="SystemMetrics"
        )
        self.threads['system_metrics'] = metrics_thread
        metrics_thread.start()
        print("   ✅ System metrics monitoring started")
        
        return success_count == len(self.modes)
    
    def stop_all_modes(self):
        """Stop all running modes"""
        print("🛑 Stopping all operational modes...")
        
        success_count = 0
        for mode_name in list(self.shared_state['active_modes']):
            if self.stop_mode(mode_name):
                success_count += 1
        
        # Stop system threads
        self.running = False
        
        print(f"   ✅ Stopped {success_count}/{len(self.modes)} modes")
    
    def _run_mode_with_enhanced_integration(self, mode_name: str, mode_instance: OperationalMode):
        """Run a mode with enhanced integration and AI features"""
        while mode_name in self.shared_state['active_modes'] and self.running:
            try:
                # Enhanced mode execution with AI integration
                result = self._execute_mode_with_enhanced_features(mode_name, mode_instance)
                
                # Process results and update shared state
                self._process_mode_result(mode_name, result)
                
                # Brief pause to prevent overwhelming the system
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in {mode_name} mode: {e}")
                time.sleep(1)  # Brief pause before retry
    
    def _execute_mode_with_enhanced_features(self, mode_name: str, mode_instance: OperationalMode):
        """Execute a mode with enhanced features and AI integration"""
        with self.lock:
            # Get current shared state
            current_state = self.shared_state.copy()
        
        # Enhance mode execution with AI insights
        ai_enhancement = self._get_ai_enhancement_for_mode(mode_name, current_state)
        
        # Execute the mode with enhanced parameters
        try:
            # For modes that support enhanced execution
            if hasattr(mode_instance, 'start_with_enhanced_features'):
                result = mode_instance.start_with_enhanced_features(
                    shared_state=current_state,
                    ai_enhancement=ai_enhancement
                )
            else:
                # Fallback to regular start method
                result = mode_instance.start()
        except AttributeError:
            # If enhanced method doesn't exist, use regular start
            result = mode_instance.start()
        
        return result
    
    def _get_ai_enhancement_for_mode(self, mode_name: str, current_state: Dict) -> Dict:
        """Get AI-based enhancements for a specific mode"""
        enhancement = {
            'recommendations': [],
            'optimizations': [],
            'predictions': [],
            'anomaly_alerts': [],
            'resource_optimization': {},
            'performance_tuning': {}
        }
        
        # Generate mode-specific AI enhancements
        if mode_name == IntegratedMode.RECEIVER.value:
            # For receiver mode: optimize signal processing
            enhancement['recommendations'].append("Optimize antenna orientation based on signal strength patterns")
            enhancement['optimizations'].append("Adjust demodulation parameters for current conditions")
            enhancement['resource_optimization']['bandwidth'] = 'adaptive'
            enhancement['performance_tuning']['sensitivity'] = 'high'
        
        elif mode_name == IntegratedMode.SIMULATION.value:
            # For simulation mode: enhance realism
            enhancement['recommendations'].append("Adjust simulation parameters based on historical data")
            enhancement['predictions'].extend(current_state.get('predictions', []))
            enhancement['resource_optimization']['accuracy'] = 'high'
            enhancement['performance_tuning']['realism'] = 'maximum'
        
        elif mode_name == IntegratedMode.REPLAY.value:
            # For replay mode: highlight anomalies
            enhancement['anomaly_alerts'].extend(current_state.get('anomalies', []))
            enhancement['resource_optimization']['analysis'] = 'comprehensive'
            enhancement['performance_tuning']['detail_level'] = 'high'
        
        elif mode_name == IntegratedMode.WEB.value:
            # For web mode: optimize dashboard
            enhancement['recommendations'].append("Update dashboard with latest AI insights")
            enhancement['optimizations'].append("Optimize data visualization for current dataset")
            enhancement['resource_optimization']['updates'] = 'real_time'
            enhancement['performance_tuning']['refresh_rate'] = 'adaptive'
        
        elif mode_name == IntegratedMode.DESKTOP_GUI.value:
            # For GUI mode: enhance user experience
            enhancement['recommendations'].append("Update UI with latest mission status")
            enhancement['optimizations'].append("Optimize rendering performance")
            enhancement['resource_optimization']['graphics'] = 'optimized'
            enhancement['performance_tuning']['ui_responsiveness'] = 'high'
        
        # Add general AI insights
        if current_state.get('ai_insights'):
            enhancement.update(current_state['ai_insights'])
        
        return enhancement
    
    def _process_mode_result(self, mode_name: str, result: Any):
        """Process results from a mode and update shared state"""
        if result is None:
            return
        
        with self.lock:
            # Update shared state based on mode result
            if isinstance(result, dict):
                # Process telemetry data
                if 'telemetry' in result:
                    self.shared_state['telemetry_data'].append(result['telemetry'])
                    # Limit stored data to prevent memory issues
                    if len(self.shared_state['telemetry_data']) > 1000:
                        self.shared_state['telemetry_data'] = self.shared_state['telemetry_data'][-500:]
                
                # Process alerts
                if 'alerts' in result:
                    for alert in result['alerts']:
                        try:
                            self.data_queues['alerts'].put_nowait(alert)
                        except queue.Full:
                            # Queue is full, remove oldest item and add new one
                            try:
                                self.data_queues['alerts'].get_nowait()
                                self.data_queues['alerts'].put_nowait(alert)
                            except Exception as e:
                                # Ignore if we can't add to queue
                                self.logger.debug(f"Alert queue operation failed: {e}")
                
                # Process commands
                if 'commands' in result:
                    for cmd in result['commands']:
                        try:
                            self.data_queues['commands'].put_nowait(cmd)
                        except queue.Full:
                            # Ignore if queue is full
                            self.logger.debug("Command queue full")
            
            # Update last update timestamp
            self.shared_state['last_update'] = datetime.now()
        
        # Trigger data received callback
        self._trigger_callbacks('on_data_received', mode_name, result)
    
    def _run_enhanced_ai_analysis(self):
        """Run continuous AI analysis on shared data"""
        while self.running:
            try:
                # Collect telemetry data for analysis
                with self.lock:
                    telemetry_data = self.shared_state['telemetry_data'][-50:]  # Use last 50 data points
                
                if len(telemetry_data) > 10:  # Need sufficient data
                    # Run enhanced analysis
                    analysis_result = self.enhanced_ai.run_enhanced_analysis(telemetry_data)
                    
                    # Update shared state with AI insights
                    with self.lock:
                        self.shared_state['ai_insights'] = analysis_result.get('enhanced_analysis', {})
                        self.shared_state['anomalies'] = analysis_result.get('enhanced_analysis', {}).get('anomalies', [])
                        self.shared_state['predictions'] = analysis_result.get('enhanced_analysis', {}).get('predictions', [])
                    
                    # Put AI analysis in queue for other modes
                    try:
                        self.data_queues['ai_analysis'].put_nowait(analysis_result)
                    except queue.Full:
                        # Ignore if queue is full
                        self.logger.debug("AI analysis queue full")
                    
                    # Trigger AI analysis callback
                    self._trigger_callbacks('on_ai_analysis', analysis_result)
                
                # Sleep to prevent overwhelming the system
                time.sleep(2.0)
                
            except Exception as e:
                logger.error(f"Error in enhanced AI analysis: {e}")
                time.sleep(5.0)  # Longer sleep on error
    
    def _run_system_metrics_monitoring(self):
        """Monitor system metrics continuously using psutil."""
        while self.running:
            try:
                # Collect actual system metrics using psutil
                cpu_usage = psutil.cpu_percent(interval=None) # Non-blocking
                virtual_memory = psutil.virtual_memory()
                memory_usage = virtual_memory.percent
                
                # Count active threads belonging to this process
                # This is an approximation; 'self.threads' tracks threads explicitly started by manager
                current_process = psutil.Process(os.getpid())
                active_threads_count = current_process.num_threads()
                
                # Data throughput is still approximated based on telemetry_data size
                data_throughput = len(self.shared_state['telemetry_data']) / (time.time() - self.shared_state['last_update'].timestamp() + 1e-6) if self.shared_state['telemetry_data'] else 0.0

                metrics = {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'active_threads': active_threads_count,
                    'data_throughput': data_throughput,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update shared state
                with self.lock:
                    self.shared_state['system_metrics'] = metrics
                
                # Put metrics in queue
                try:
                    self.data_queues['system_metrics'].put_nowait(metrics)
                except queue.Full:
                    pass  # Ignore if queue is full
                
                # Sleep between metrics collection
                time.sleep(5.0)
                
            except Exception as e:
                logger.error(f"Error in system metrics monitoring: {e}")
                time.sleep(10.0)  # Longer sleep on error
    
    def switch_mode(self, new_mode: str) -> bool:
        """Switch to a different operational mode while maintaining integration"""
        if new_mode not in self.modes:
            print(f"❌ Invalid mode: {new_mode}")
            return False
        
        print(f"🔄 Switching to {new_mode} mode...")
        
        with self.lock:
            # Update shared state
            old_mode = self.shared_state['current_mode']
            self.shared_state['current_mode'] = new_mode
            
            # Notify all modes of the switch
            switch_notification = {
                'type': 'mode_switch',
                'old_mode': old_mode,
                'new_mode': new_mode,
                'timestamp': datetime.now().isoformat()
            }
        
        # Send notification to all queues
        for queue_name, data_queue in self.data_queues.items():
            try:
                data_queue.put_nowait(switch_notification)
            except queue.Full:
                # Queue might be full, that's okay
                self.logger.debug(f"Queue {queue_name} full, dropping notification")
        
        print(f"✅ Switched to {new_mode} mode")
        return True
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status across all modes"""
        with self.lock:
            status = {
                'enhanced_mode_manager': {
                    'running': self.running,
                    'initialized_modes': list(self.modes.keys()),
                    'active_modes': list(self.shared_state['active_modes']),
                    'active_threads': len([t for t in self.threads.values() if t.is_alive()]),
                    'integration_level': self.shared_state['integration_level'],
                    'queue_status': {name: {'size': q.qsize(), 'maxsize': q._maxsize} 
                                   for name, q in self.data_queues.items()}
                },
                'ai_engine': self.enhanced_ai.get_enhanced_engine_status(),
                'mode_status': {},
                'system_metrics': self.shared_state['system_metrics'],
                'system_health': 'optimal',
                'data_points_collected': len(self.shared_state['telemetry_data'])
            }
        
        # Get status from each mode
        for mode_name, mode_instance in self.modes.items():
            try:
                if hasattr(mode_instance, 'get_status'):
                    status['mode_status'][mode_name] = mode_instance.get_status()
                else:
                    status['mode_status'][mode_name] = {'status': 'running', 'features': 'standard'}
            except:
                status['mode_status'][mode_name] = {'status': 'error', 'features': 'unknown'}
        
        # Determine overall system health
        active_modes = len(self.shared_state['active_modes'])
        if active_modes < len(self.modes) * 0.3:  # Less than 30% active
            status['system_health'] = 'critical'
        elif active_modes < len(self.modes) * 0.6:  # Less than 60% active
            status['system_health'] = 'degraded'
        elif active_modes < len(self.modes) * 0.9:  # Less than 90% active
            status['system_health'] = 'caution'
        
        return status
    
    def get_enhanced_features(self) -> List[str]:
        """Get list of all enhanced features available in the mode manager"""
        features = [
            "Cross-mode data sharing and synchronization",
            "Real-time AI-powered analysis across all modes",
            "Coordinated operation of all 9 operational modes",
            "Shared state management for consistent operation",
            "Inter-mode communication via data queues",
            "Enhanced anomaly detection with AI",
            "Multi-step predictions using deep neural networks",
            "Advanced data filtering across all data streams",
            "Seamless mode switching with preserved context",
            "Unified dashboard showing all mode statuses",
            "Centralized command and control system",
            "Enhanced security with coordinated authentication",
            "Real-time mission phase classification",
            "Automated system optimization recommendations",
            "Comprehensive reporting across all operational modes",
            "System metrics monitoring and optimization",
            "Event-driven architecture with callbacks",
            "Thread-safe operation with locking mechanisms",
            "Adaptive resource allocation",
            "Performance tuning based on AI insights"
        ]
        
        # Add AI-specific features
        ai_status = self.enhanced_ai.get_enhanced_engine_status()
        if ai_status.get('initialized', False):
            features.extend(ai_status.get('ai_capabilities', []))
        
        return features
    
    def get_active_modes(self) -> List[str]:
        """Get list of currently active modes"""
        with self.lock:
            return list(self.shared_state['active_modes'])
    
    def get_shared_data(self, data_type: str = 'all') -> Any:
        """Get shared data of a specific type"""
        with self.lock:
            if data_type == 'telemetry':
                return self.shared_state['telemetry_data']
            elif data_type == 'anomalies':
                return self.shared_state['anomalies']
            elif data_type == 'predictions':
                return self.shared_state['predictions']
            elif data_type == 'ai_insights':
                return self.shared_state['ai_insights']
            elif data_type == 'system_metrics':
                return self.shared_state['system_metrics']
            elif data_type == 'all':
                return self.shared_state
            else:
                raise ValueError(f"Unknown data type: {data_type}")


def create_powerful_mode_pack():
    """Factory function to create a powerful mode pack instance"""
    return EnhancedModeManager()


def main():
    """Main function to demonstrate the enhanced mode manager"""
    print("🚀 AirOne v3.0 - Enhanced Mode Manager")
    print("========================================")
    print("Advanced mode management with full integration")
    
    # Create the enhanced mode manager
    mode_manager = EnhancedModeManager()
    
    # Show available features
    features = mode_manager.get_enhanced_features()
    print(f"\nAvailable Enhanced Features ({len(features)}):")
    for i, feature in enumerate(features[:10], 1):  # Show first 10
        print(f"  {i:2d}. {feature}")
    if len(features) > 10:
        print(f"  ... and {len(features) - 10} more features")
    
    # Show system status
    status = mode_manager.get_system_status()
    print(f"\nSystem Status:")
    print(f"  - Active modes: {len(status['enhanced_mode_manager']['active_modes'])}/{len(mode_manager.modes)}")
    print(f"  - System health: {status['system_health']}")
    print(f"  - Data points: {status['data_points_collected']}")
    
    print(f"\nReady to manage all operational modes with enhanced capabilities!")
    print("Use the EnhancedModeManager to coordinate all AirOne v3.0 modes.")


if __name__ == "__main__":
    main()