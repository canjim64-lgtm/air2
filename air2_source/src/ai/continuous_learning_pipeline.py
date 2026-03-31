"""
AirOne v4.0 - Continuous Learning Pipeline
Orchestrates continuous model training from flight simulation data
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import pickle
import os
import logging
import threading
import time
from dataclasses import dataclass, asdict
from queue import Queue, Empty
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from .self_training_flight_model import SelfTrainingFlightModel, FlightModelState, TrainingMetrics
from .flight_data_simulator import FlightDataSimulator, FlightTelemetry


class PipelineStatus(Enum):
    """Pipeline operational status"""
    IDLE = "idle"
    RUNNING = "running"
    TRAINING = "training"
    PAUSED = "paused"
    ERROR = "error"


class DataStrategy(Enum):
    """Data handling strategies"""
    STREAM = "stream"  # Process data in real-time
    BATCH = "batch"    # Accumulate and process in batches
    HYBRID = "hybrid"  # Stream with periodic batch training


@dataclass
class PipelineConfig:
    """Configuration for the learning pipeline"""
    # Data settings
    buffer_size: int = 10000
    batch_size: int = 500
    data_strategy: str = "hybrid"
    
    # Training settings
    min_samples_initial: int = 500
    min_samples_retrain: int = 200
    training_interval_seconds: int = 60
    validation_split: float = 0.2
    
    # Model settings
    model_type: str = "ensemble"
    prediction_targets: List[str] = None
    
    # Performance settings
    performance_threshold: float = 0.7
    degradation_threshold: float = 0.05
    
    # Simulation settings
    simulation_enabled: bool = True
    simulation_speed: float = 1.0  # 1.0 = real-time
    
    # Persistence
    save_dir: str = "models/flight_model"
    auto_save: bool = True
    save_interval_seconds: int = 300
    
    def __post_init__(self):
        if self.prediction_targets is None:
            self.prediction_targets = ['altitude', 'velocity', 'battery_percentage']


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    status: str
    uptime_seconds: float
    total_samples_processed: int
    total_training_sessions: int
    last_training_time: Optional[str]
    current_model_version: int
    model_accuracy: float
    prediction_latency_ms: float
    data_buffer_utilization: float
    simulation_samples_generated: int


class ContinuousLearningPipeline:
    """
    Continuous learning pipeline for flight models
    
    Orchestrates data collection, model training, and deployment
    in a continuous loop
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.model = SelfTrainingFlightModel({
            'model_type': self.config.model_type,
            'training_mode': 'online',
            'prediction_targets': self.config.prediction_targets,
            'min_samples': self.config.min_samples_initial,
            'training_interval': self.config.training_interval_seconds,
            'validation_split': self.config.validation_split,
            'buffer_size': self.config.buffer_size
        })
        
        self.simulator = FlightDataSimulator({
            'simulation_rate': 10,
            'aircraft': {'mass': 1.5, 'battery_capacity': 5000}
        })
        
        # Data pipeline
        self.data_queue = Queue(maxsize=self.config.buffer_size)
        self.processed_count = 0
        self.simulation_count = 0
        
        # Training state
        self.status = PipelineStatus.IDLE
        self.start_time = None
        self.last_training_time = None
        self.training_thread = None
        self.stop_flag = False
        
        # Callbacks
        self.on_sample_callback: Optional[Callable] = None
        self.on_training_callback: Optional[Callable] = None
        self.on_prediction_callback: Optional[Callable] = None
        
        # Metrics
        self.metrics_history: List[PipelineMetrics] = []
        self.prediction_latencies: List[float] = []
        
        # Ensure save directory exists
        if self.config.auto_save:
            os.makedirs(self.config.save_dir, exist_ok=True)
        
        logger.info("Continuous Learning Pipeline initialized")

    def start(self, initial_training: bool = True):
        """
        Start the learning pipeline
        
        Args:
            initial_training: Whether to perform initial training
        """
        if self.status == PipelineStatus.RUNNING:
            logger.warning("Pipeline already running")
            return
        
        logger.info("Starting Continuous Learning Pipeline...")
        self.start_time = datetime.now()
        self.stop_flag = False
        
        # Generate initial dataset if enabled
        if self.config.simulation_enabled and initial_training:
            logger.info("Generating initial training dataset...")
            self._generate_initial_dataset()
        
        # Start background training thread
        self.training_thread = threading.Thread(target=self._training_loop, daemon=True)
        self.training_thread.start()
        
        self.status = PipelineStatus.RUNNING
        logger.info("✅ Pipeline started")

    def stop(self):
        """Stop the learning pipeline"""
        logger.info("Stopping pipeline...")
        self.stop_flag = True
        self.status = PipelineStatus.IDLE
        
        if self.training_thread:
            self.training_thread.join(timeout=5)
        
        # Save model
        if self.config.auto_save:
            self.save_model()
        
        logger.info("Pipeline stopped")

    def _generate_initial_dataset(self, n_flights: int = 5):
        """Generate initial training dataset from simulation"""
        dataset = self.simulator.generate_labeled_dataset(
            n_flights=n_flights,
            duration_range=(60, 180),
            include_anomalies=True
        )
        
        # Feed to model
        for record in dataset:
            self.ingest_sample(record)
        
        # Initial training
        logger.info(f"Performing initial training with {len(dataset)} samples...")
        self.model.trigger_training()
        
        self.simulation_count = len(dataset)
        logger.info(f"✅ Initial dataset: {len(dataset)} samples")

    def ingest_sample(self, telemetry: Dict[str, Any]):
        """
        Ingest a single telemetry sample
        
        Args:
            telemetry: Flight telemetry record
        """
        try:
            self.data_queue.put_nowait(telemetry)
            self.model.ingest_flight_data(telemetry)
            self.processed_count += 1
            
            if self.on_sample_callback:
                self.on_sample_callback(telemetry)
                
        except Exception as e:
            logger.error(f"Failed to ingest sample: {e}")

    def ingest_batch(self, telemetry_list: List[Dict[str, Any]]):
        """
        Ingest batch of telemetry samples
        
        Args:
            telemetry_list: List of telemetry records
        """
        for telemetry in telemetry_list:
            self.ingest_sample(telemetry)

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction from telemetry
        
        Args:
            telemetry: Current telemetry
            
        Returns:
            Prediction dictionary
        """
        start = time.time()
        
        predictions = self.model.predict(telemetry)
        
        latency = (time.time() - start) * 1000
        self.prediction_latencies.append(latency)
        
        if self.on_prediction_callback:
            self.on_prediction_callback(telemetry, predictions)
        
        return predictions

    def _training_loop(self):
        """Background training loop"""
        while not self.stop_flag:
            try:
                if self.status == PipelineStatus.RUNNING:
                    # Check if training should be triggered
                    if self.model._should_train():
                        self.status = PipelineStatus.TRAINING
                        
                        metrics = self.model.trigger_training()
                        
                        if metrics:
                            self.last_training_time = datetime.now()
                            
                            if self.on_training_callback:
                                self.on_training_callback(metrics)
                            
                            # Auto-save after training
                            if self.config.auto_save:
                                self.save_model()
                        
                        self.status = PipelineStatus.RUNNING
                
                # Check for auto-save
                if (self.config.auto_save and 
                    self.last_training_time and
                    (datetime.now() - self.last_training_time).total_seconds() > self.config.save_interval_seconds):
                    self.save_model()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Training loop error: {e}")
                self.status = PipelineStatus.ERROR
                time.sleep(5)

    def run_simulation(self, duration_seconds: float, 
                       real_time: bool = False) -> List[Dict]:
        """
        Run flight simulation and collect data
        
        Args:
            duration_seconds: Simulation duration
            real_time: Whether to run in real-time
            
        Returns:
            List of generated telemetry records
        """
        logger.info(f"Starting simulation: {duration_seconds}s...")
        
        telemetry_list = self.simulator.generate_flight_sequence(
            duration_seconds,
            include_anomalies=True
        )
        
        for telemetry_record in telemetry_list:
            record_dict = asdict(telemetry_record) if hasattr(telemetry_record, '__dataclass_fields__') else telemetry_record
            
            # Ingest into pipeline
            self.ingest_sample(record_dict)
            self.simulation_count += 1
            
            # Make predictions
            predictions = self.predict(record_dict)
            
            if real_time:
                time.sleep(1.0 / self.simulator.simulation_rate)
        
        logger.info(f"✅ Simulation complete: {len(telemetry_list)} samples")
        return [asdict(t) if hasattr(t, '__dataclass_fields__') else t for t in telemetry_list]

    def get_metrics(self) -> PipelineMetrics:
        """Get current pipeline metrics"""
        model_state = self.model.get_state()
        
        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        avg_latency = np.mean(self.prediction_latencies[-100:]) if self.prediction_latencies else 0
        
        buffer_util = self.model.buffer.size() / self.config.buffer_size
        
        metrics = PipelineMetrics(
            status=self.status.value,
            uptime_seconds=uptime,
            total_samples_processed=self.processed_count,
            total_training_sessions=len(self.model.training_history),
            last_training_time=self.last_training_time.isoformat() if self.last_training_time else None,
            current_model_version=model_state.model_version if model_state else 0,
            model_accuracy=model_state.accuracy_score if model_state else 0,
            prediction_latency_ms=avg_latency,
            data_buffer_utilization=buffer_util,
            simulation_samples_generated=self.simulation_count
        )
        
        self.metrics_history.append(metrics)
        
        return metrics

    def save_model(self, filepath: Optional[str] = None) -> bool:
        """Save model to file"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(self.config.save_dir, f"flight_model_v{self.model.model_version}_{timestamp}.pkl")
        
        return self.model.save_model(filepath)

    def load_model(self, filepath: str) -> bool:
        """Load model from file"""
        return self.model.load_model(filepath)

    def load_latest_model(self) -> bool:
        """Load the latest saved model"""
        if not os.path.exists(self.config.save_dir):
            return False
        
        model_files = [
            f for f in os.listdir(self.config.save_dir)
            if f.endswith('.pkl') and f.startswith('flight_model')
        ]
        
        if not model_files:
            logger.info("No saved models found")
            return False
        
        # Get latest file
        latest_file = max(model_files, key=lambda f: os.path.getmtime(os.path.join(self.config.save_dir, f)))
        filepath = os.path.join(self.config.save_dir, latest_file)
        
        logger.info(f"Loading latest model: {latest_file}")
        return self.load_model(filepath)

    def export_training_report(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive training report"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(self.config.save_dir, f"training_report_{timestamp}.json")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'pipeline_metrics': asdict(self.get_metrics()),
            'model_state': asdict(self.model.get_state()) if self.model.get_state() else {},
            'training_history': [asdict(m) for m in self.model.training_history],
            'config': asdict(self.config),
            'performance_summary': self.model.get_performance_report()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Training report exported to {filepath}")
        return report

    def set_callbacks(self, 
                     on_sample: Optional[Callable] = None,
                     on_training: Optional[Callable] = None,
                     on_prediction: Optional[Callable] = None):
        """Set pipeline callbacks"""
        self.on_sample_callback = on_sample
        self.on_training_callback = on_training
        self.on_prediction_callback = on_prediction

    def get_status_summary(self) -> Dict[str, Any]:
        """Get human-readable status summary"""
        metrics = self.get_metrics()
        model_state = self.model.get_state()
        
        return {
            'status': metrics.status,
            'uptime': f"{metrics.uptime_seconds:.0f}s",
            'samples_processed': metrics.total_samples_processed,
            'simulation_samples': metrics.simulation_samples_generated,
            'model_version': metrics.current_model_version,
            'model_accuracy': f"{metrics.model_accuracy:.2%}",
            'training_sessions': metrics.total_training_sessions,
            'last_training': metrics.last_training_time or 'never',
            'buffer_usage': f"{metrics.data_buffer_utilization:.1%}",
            'prediction_latency': f"{metrics.prediction_latency_ms:.2f}ms",
            'performance_trend': model_state.performance_trend if model_state else 'unknown'
        }


# Convenience function
def create_learning_pipeline(config: Optional[PipelineConfig] = None) -> ContinuousLearningPipeline:
    """Create and return a Continuous Learning Pipeline instance"""
    return ContinuousLearningPipeline(config)


__all__ = [
    'ContinuousLearningPipeline',
    'create_learning_pipeline',
    'PipelineConfig',
    'PipelineMetrics',
    'PipelineStatus',
    'DataStrategy'
]
