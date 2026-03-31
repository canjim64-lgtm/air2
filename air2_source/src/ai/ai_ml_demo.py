"""
AirOne v4.0 - AI/ML Features Demo
Demonstrates the new enhanced AI/ML capabilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import random


def generate_sample_telemetry(n_samples=100):
    """Generate sample telemetry data for testing"""
    telemetry = []
    base_altitude = 0
    base_velocity = 0
    
    for i in range(n_samples):
        # Simulate ascent phase
        if i < 30:
            base_altitude += random.uniform(100, 200)
            base_velocity = random.uniform(20, 50)
        # Simulate apogee
        elif i < 50:
            base_altitude += random.uniform(-20, 50)
            base_velocity = random.uniform(-10, 10)
        # Simulate descent
        else:
            base_altitude -= random.uniform(50, 150)
            base_velocity = random.uniform(-30, -10)
        
        base_altitude = max(0, min(10000, base_altitude))
        
        telemetry.append({
            'timestamp': datetime.now().isoformat(),
            'altitude': base_altitude + random.uniform(-50, 50),
            'velocity': base_velocity + random.uniform(-5, 5),
            'temperature': random.uniform(15, 35),
            'pressure': random.uniform(95000, 105000),
            'battery_level': max(0, 100 - i * 0.5),
            'latitude': random.uniform(40.0, 41.0),
            'longitude': random.uniform(-74.0, -73.0),
            'radio_signal_strength': random.uniform(-80, -30)
        })
    
    return telemetry


def demo_unified_ai_service():
    """Demo the Unified AI Service"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Unified AI Service Demo")
    print("="*70)
    
    try:
        from src.ai import UnifiedAIService, TaskType
        
        print("\n[1/6] Initializing Unified AI Service...")
        ai_service = UnifiedAIService()
        print("✅ Service initialized successfully")
        
        # Generate sample data
        print("\n[2/6] Generating sample telemetry data...")
        telemetry = generate_sample_telemetry(150)
        print(f"✅ Generated {len(telemetry)} telemetry records")
        
        # Train a regression model
        print("\n[3/6] Training regression model (predicting altitude)...")
        metadata = ai_service.train_model(
            telemetry, 
            TaskType.REGRESSION, 
            target_column='altitude',
            model_type='random_forest'
        )
        print(f"✅ Model trained: {metadata.model_id}")
        print(f"   - R² Score: {metadata.r2_score:.4f}" if metadata.r2_score else "   - Training completed")
        
        # Make predictions
        print("\n[4/6] Making predictions...")
        test_data = telemetry[-5:]
        predictions = ai_service.predict(metadata.model_id, test_data)
        print(f"✅ Generated {len(predictions.predictions)} predictions")
        print(f"   - Inference time: {predictions.inference_time_ms:.2f}ms")
        print(f"   - Sample prediction: {predictions.predictions[0]:.2f}")
        
        # Anomaly detection
        print("\n[5/6] Running anomaly detection...")
        anomalies = ai_service.detect_anomalies(telemetry)
        print(f"✅ Detected {len(anomalies)} anomalies")
        if anomalies:
            print(f"   - Most severe anomaly score: {anomalies[0]['anomaly_score']:.4f}")
        
        # Generate report
        print("\n[6/6] Generating analysis report...")
        report = ai_service.generate_analysis_report(telemetry[:50])
        print(f"✅ Report generated ({len(report)} characters)")
        
        # Service status
        print("\n📊 Service Status:")
        status = ai_service.get_status()
        for key, value in status.items():
            print(f"   - {key}: {value}")
        
        print("\n✅ Unified AI Service Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_automl_selector():
    """Demo the AutoML Selector"""
    print("\n" + "="*70)
    print("AirOne v4.0 - AutoML Selector Demo")
    print("="*70)
    
    try:
        from src.ml import AutoMLSelector
        import numpy as np
        
        print("\n[1/4] Initializing AutoML Selector...")
        automl = AutoMLSelector(task_type='regression', cv_folds=3)
        print("✅ AutoML Selector initialized")
        
        # Generate sample data
        print("\n[2/4] Generating sample dataset...")
        np.random.seed(42)
        X = np.random.randn(200, 8)
        y = 2*X[:, 0] + 3*X[:, 1]**2 + np.random.randn(200) * 0.5
        print(f"✅ Dataset: {X.shape[0]} samples, {X.shape[1]} features")
        
        # Evaluate models
        print("\n[3/4] Evaluating ML models (this may take a moment)...")
        results = automl.evaluate_models(X, y)
        print(f"✅ Evaluated {len(results)} models")
        
        # Show results
        print("\n[4/4] Model Performance Summary:")
        print("-"*50)
        
        # Sort by R² score
        sorted_models = sorted(results.items(), key=lambda x: x[1].r2_score or 0, reverse=True)
        
        for i, (name, perf) in enumerate(sorted_models[:5], 1):
            print(f"\n{i}. {name}")
            print(f"   Category: {perf.model_category}")
            print(f"   R² Score: {perf.r2_score:.4f}")
            print(f"   RMSE: {perf.rmse:.4f}" if perf.rmse else "   RMSE: N/A")
            print(f"   Training Time: {perf.training_time:.2f}s")
        
        print("\n✅ AutoML Selector Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_ai_config_manager():
    """Demo the AI/ML Configuration Manager"""
    print("\n" + "="*70)
    print("AirOne v4.0 - AI/ML Configuration Manager Demo")
    print("="*70)
    
    try:
        from src.ai import AIMLConfigManager
        
        print("\n[1/4] Initializing Configuration Manager...")
        config_mgr = AIMLConfigManager()
        print("✅ Configuration Manager initialized")
        
        # Get configuration values
        print("\n[2/4] Reading configuration values...")
        print(f"   - Cache enabled: {config_mgr.get('general.enable_caching')}")
        print(f"   - Default test size: {config_mgr.get('training.default_test_size')}")
        print(f"   - GPU enabled: {config_mgr.get('resources.gpu_enabled')}")
        print(f"   - DeepSeek enabled: {config_mgr.get('deepseek.enabled')}")
        
        # Update configuration
        print("\n[3/4] Updating configuration...")
        config_mgr.set('training.random_state', 123)
        config_mgr.set('models.random_forest.regression.n_estimators', 200)
        config_mgr.set('deepseek.temperature', 0.8)
        print("✅ Configuration updated")
        
        # Get model config
        print("\n[4/4] Model-specific configuration:")
        rf_config = config_mgr.get_model_config('random_forest', 'regression')
        print(f"   Random Forest (Regression) config:")
        for key, value in rf_config.items():
            print(f"      - {key}: {value}")
        
        # Config summary
        print("\n📋 Configuration Summary:")
        summary = config_mgr.get_config_summary()
        for key, value in summary.items():
            print(f"   - {key}: {value}")
        
        print("\n✅ Configuration Manager Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_ensemble_builder():
    """Demo the Ensemble Model Builder"""
    print("\n" + "="*70)
    print("AirOne v4.0 - Ensemble Model Builder Demo")
    print("="*70)
    
    try:
        from src.ml import EnsembleModelBuilder
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score
        
        print("\n[1/5] Initializing Ensemble Model Builder...")
        builder = EnsembleModelBuilder()
        print("✅ Ensemble Builder initialized")
        
        # Generate sample data
        print("\n[2/5] Generating sample dataset...")
        np.random.seed(42)
        X = np.random.randn(300, 6)
        y = 2*X[:, 0] + X[:, 1]**2 + 0.5*X[:, 2]*X[:, 3] + np.random.randn(300) * 0.3
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print(f"✅ Dataset: {X_train.shape[0]} training, {X_test.shape[0]} test samples")
        
        # Create stacking ensemble
        print("\n[3/5] Creating Stacking Ensemble...")
        stacking_model = builder.create_stacking_ensemble(X_train, y_train, task_type='regression')
        y_pred_stack = stacking_model.predict(X_test)
        r2_stack = r2_score(y_test, y_pred_stack)
        print(f"✅ Stacking Ensemble - R² Score: {r2_stack:.4f}")
        
        # Create voting ensemble
        print("\n[4/5] Creating Voting Ensemble...")
        voting_model = builder.create_voting_ensemble(X_train, y_train, task_type='regression')
        y_pred_vote = voting_model.predict(X_test)
        r2_vote = r2_score(y_test, y_pred_vote)
        print(f"✅ Voting Ensemble - R² Score: {r2_vote:.4f}")
        
        # Compare results
        print("\n[5/5] Ensemble Comparison:")
        print("-"*50)
        print(f"   Stacking Ensemble R²: {r2_stack:.4f}")
        print(f"   Voting Ensemble R²:   {r2_vote:.4f}")
        print(f"   Best approach: {'Stacking' if r2_stack > r2_vote else 'Voting'}")
        
        print("\n✅ Ensemble Model Builder Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_demos():
    """Run all AI/ML demos"""
    print("\n" + "="*70)
    print("AirOne Professional v4.0 - AI/ML Features Demo Suite")
    print("="*70)
    print("\nRunning all AI/ML feature demonstrations...\n")
    
    results = []
    
    # Run demos
    results.append(("Unified AI Service", demo_unified_ai_service()))
    results.append(("AutoML Selector", demo_automl_selector()))
    results.append(("Configuration Manager", demo_ai_config_manager()))
    results.append(("Ensemble Builder", demo_ensemble_builder()))
    
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
