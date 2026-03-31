"""
AirOne v4.0 - Self-Training Flight Model Demo
Demonstrates autonomous model training on flight simulation data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
import json


def demo_self_training_model():
    """Demo the Self-Training Flight Model"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Self-Training Flight Model Demo")
    print("="*70)
    
    try:
        from src.ai import (
            SelfTrainingFlightModel,
            FlightDataSimulator,
            FlightPhase
        )
        
        print("\n[1/5] Initializing Flight Data Simulator...")
        simulator = FlightDataSimulator({
            'simulation_rate': 10,
            'start_altitude': 10,
            'base_temperature': 20,
            'wind_speed': 5
        })
        print("✅ Flight simulator initialized")
        
        print("\n[2/5] Initializing Self-Training Flight Model...")
        model = SelfTrainingFlightModel({
            'model_type': 'ensemble',
            'training_mode': 'online',
            'prediction_targets': ['altitude', 'velocity', 'battery_percentage'],
            'min_samples': 100,
            'training_interval': 30,
            'buffer_size': 5000
        })
        model.initialize()
        print("✅ Self-Training model initialized")
        
        print("\n[3/5] Generating initial training dataset...")
        initial_data = simulator.generate_labeled_dataset(
            n_flights=3,
            duration_range=(30, 60),
            include_anomalies=True
        )
        print(f"✅ Generated {len(initial_data)} initial samples")
        
        # Ingest initial data
        for record in initial_data:
            model.ingest_flight_data(record)
        
        print("\n[4/5] Training initial model...")
        training_result = model.trigger_training()
        if training_result:
            print(f"✅ Initial training completed")
            print(f"   - Samples used: {training_result.samples_used}")
            print(f"   - Validation score: {training_result.validation_score:.4f}")
            print(f"   - Improvement: {training_result.improvement:.4f}")
        
        print("\n[5/5] Running live simulation with predictions...")
        print("-"*50)
        
        # Run simulation and make predictions
        simulator.reset()
        n_steps = 50
        
        predictions_made = 0
        actual_values = []
        predicted_values = []
        
        for i in range(n_steps):
            # Generate telemetry
            telemetry = simulator.generate_telemetry()
            telemetry_dict = {
                'altitude': telemetry.altitude,
                'velocity': telemetry.velocity,
                'battery_percentage': telemetry.battery_percentage,
                'throttle': telemetry.throttle,
                'pitch': telemetry.pitch,
                'climb_rate': telemetry.climb_rate
            }
            
            # Make predictions
            predictions = model.predict(telemetry_dict)
            
            # Track accuracy
            if 'predicted_altitude' in predictions:
                predictions_made += 1
                actual_values.append(telemetry.altitude)
                predicted_values.append(predictions['predicted_altitude'])
            
            # Ingest new data for continuous learning
            model.ingest_flight_data(telemetry_dict)
            
            # Print progress every 10 steps
            if i % 10 == 0:
                state = model.get_state()
                print(f"  Step {i+1}/{n_steps}:")
                print(f"    Altitude: {telemetry.altitude:.1f}m (predicted: {predictions.get('predicted_altitude', 'N/A')})")
                print(f"    Model accuracy: {state.accuracy_score:.2%}" if state else "    Model training...")
                print(f"    Buffer size: {model.buffer.size()} samples")
            
            time.sleep(0.05)  # Small delay for readability
        
        # Calculate prediction accuracy
        if actual_values and predicted_values:
            errors = [abs(a - p) for a, p in zip(actual_values, predicted_values)]
            avg_error = sum(errors) / len(errors)
            print(f"\n📊 Prediction Summary:")
            print(f"   - Predictions made: {predictions_made}")
            print(f"   - Mean absolute error: {avg_error:.2f}m")
            print(f"   - Model version: {model.model_version}")
        
        # Get final state
        state = model.get_state()
        if state:
            print(f"\n📈 Final Model State:")
            print(f"   - Total samples: {state.total_samples}")
            print(f"   - Training iterations: {state.training_iterations}")
            print(f"   - Model version: {state.model_version}")
            print(f"   - Accuracy: {state.accuracy_score:.2%}")
            print(f"   - Performance trend: {state.performance_trend}")
        
        # Get performance report
        report = model.get_performance_report()
        print(f"\n📋 Performance Report:")
        print(f"   - Target performance:")
        for target, perf in report.get('target_performance', {}).items():
            print(f"      {target}: R² = {perf['r2_score']:.4f}")
        print(f"   - Buffer utilization: {report['buffer_status']['utilization']:.1%}")
        
        print("\n✅ Self-Training Flight Model Demo completed!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_continuous_learning_pipeline():
    """Demo the Continuous Learning Pipeline"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Continuous Learning Pipeline Demo")
    print("="*70)
    
    try:
        from src.ai import (
            ContinuousLearningPipeline,
            PipelineConfig
        )
        
        print("\n[1/4] Creating pipeline configuration...")
        config = PipelineConfig(
            buffer_size=5000,
            batch_size=200,
            min_samples_initial=200,
            training_interval_seconds=30,
            simulation_enabled=True,
            auto_save=False
        )
        print("✅ Configuration created")
        
        print("\n[2/4] Initializing pipeline...")
        pipeline = ContinuousLearningPipeline(config)
        print("✅ Pipeline initialized")
        
        print("\n[3/4] Starting pipeline with initial training...")
        pipeline.start(initial_training=True)
        
        # Wait for initial training
        time.sleep(2)
        
        print("\n[4/4] Running simulation...")
        telemetry_list = pipeline.run_simulation(
            duration_seconds=30,
            real_time=False
        )
        
        # Get metrics
        metrics = pipeline.get_metrics()
        print(f"\n📊 Pipeline Metrics:")
        print(f"   - Status: {metrics.status}")
        print(f"   - Uptime: {metrics.uptime_seconds:.1f}s")
        print(f"   - Samples processed: {metrics.total_samples_processed}")
        print(f"   - Simulation samples: {metrics.simulation_samples_generated}")
        print(f"   - Model version: {metrics.current_model_version}")
        print(f"   - Model accuracy: {metrics.model_accuracy:.2%}")
        print(f"   - Training sessions: {metrics.total_training_sessions}")
        print(f"   - Buffer utilization: {metrics.data_buffer_utilization:.1%}")
        
        # Get status summary
        summary = pipeline.get_status_summary()
        print(f"\n📋 Status Summary:")
        for key, value in summary.items():
            print(f"   - {key}: {value}")
        
        # Stop pipeline
        pipeline.stop()
        
        print("\n✅ Continuous Learning Pipeline Demo completed!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_performance_monitor():
    """Demo the Model Performance Monitor"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Model Performance Monitor Demo")
    print("="*70)
    
    try:
        from src.ai import (
            PerformanceMonitor,
            ModelEvaluator,
            AlertLevel
        )
        
        print("\n[1/3] Initializing Performance Monitor...")
        monitor = PerformanceMonitor({
            'short_window': 20,
            'medium_window': 50,
            'drift_threshold': 0.1,
            'alert_cooldown': 10
        })
        print("✅ Performance Monitor initialized")
        
        print("\n[2/3] Simulating predictions and recording...")
        
        # Simulate predictions with varying accuracy
        import random
        n_predictions = 100
        
        for i in range(n_predictions):
            # Generate prediction
            prediction = {
                'predicted_altitude': 100 + random.uniform(-5, 5),
                'predicted_velocity': 20 + random.uniform(-2, 2),
                'predicted_battery': 80 + random.uniform(-3, 3)
            }
            
            # Generate actual (with some drift)
            drift = min(i / n_predictions, 0.2)  # Increasing drift
            actual = {
                'altitude': 100 + random.uniform(-5 - drift*10, 5 + drift*10),
                'velocity': 20 + random.uniform(-2 - drift*5, 2 + drift*5),
                'battery': 80 + random.uniform(-3, 3)
            }
            
            # Record
            monitor.record_prediction(
                prediction=prediction,
                actual=actual,
                latency_ms=random.uniform(5, 20)
            )
        
        print(f"✅ Recorded {n_predictions} predictions")
        
        print("\n[3/3] Getting performance metrics...")
        metrics = monitor.get_current_metrics()
        
        print(f"\n📊 Current Metrics:")
        print(f"   - Status: {metrics.get('status', 'unknown')}")
        print(f"   - Samples recorded: {metrics.get('samples_recorded', 0)}")
        print(f"   - Errors recorded: {metrics.get('errors_recorded', 0)}")
        
        # Accuracy metrics
        for metric in ['altitude', 'velocity', 'battery_percentage']:
            if f'{metric}_accuracy_mean' in metrics:
                print(f"   - {metric} accuracy: {metrics[f'{metric}_accuracy_mean']:.2%}")
        
        # Latency metrics
        if 'latency_mean_ms' in metrics:
            print(f"   - Latency: {metrics['latency_mean_ms']:.2f}ms (max: {metrics['latency_max_ms']:.2f}ms)")
        
        # Alerts
        alerts = monitor.get_active_alerts()
        print(f"\n🚨 Active Alerts: {len(alerts)}")
        for alert in alerts:
            print(f"   - [{alert.level}] {alert.message}")
        
        # Performance trend
        trend = monitor.get_performance_trend(window_minutes=60)
        print(f"\n📈 Performance Trend: {trend.get('trend', 'unknown')}")
        
        print("\n✅ Performance Monitor Demo completed!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_demos():
    """Run all self-training demos"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Self-Training Flight Model Demo Suite")
    print("="*70)
    print("\nRunning all self-training feature demonstrations...\n")
    
    results = []
    
    results.append(("Self-Training Model", demo_self_training_model()))
    results.append(("Continuous Learning Pipeline", demo_continuous_learning_pipeline()))
    results.append(("Performance Monitor", demo_performance_monitor()))
    
    # Summary
    print("\n" + "="*70)
    print("Demo Summary")
    print("="*70)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} - {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} demos passed")
    print("="*70)


if __name__ == "__main__":
    run_all_demos()
