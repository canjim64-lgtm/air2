"""
AirOne v4.0 - Model Registry and Versioning System
Track, version, and manage ML models in production
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
import os
import hashlib
import logging
from dataclasses import dataclass, asdict, field
from enum import Enum
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model lifecycle status"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ModelType(Enum):
    """Model types"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    DEEP_LEARNING = "deep_learning"
    ENSEMBLE = "ensemble"


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_id: str
    model_name: str
    model_type: str
    version: str
    status: str
    created_at: str
    updated_at: str
    created_by: str
    description: str
    tags: List[str]
    metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_names: List[str]
    target_name: str
    training_samples: int
    validation_samples: int
    model_hash: str
    parent_model_id: Optional[str] = None
    experiment_id: Optional[str] = None


@dataclass
class ModelVersion:
    """Model version information"""
    version: str
    created_at: str
    status: str
    metrics: Dict[str, float]
    model_path: str
    changelog: str


@dataclass
class ModelComparison:
    """Model comparison result"""
    models: List[str]
    metrics_comparison: Dict[str, Dict[str, float]]
    winner: str
    improvement: float
    recommendation: str


class ModelRegistry:
    """
    Central registry for ML models
    
    Tracks model versions, metadata, and lifecycle
    """

    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = registry_path
        self.models: Dict[str, ModelMetadata] = {}
        self.model_artifacts: Dict[str, Any] = {}
        self.version_history: Dict[str, List[ModelVersion]] = defaultdict(list)
        
        # Create registry directory
        os.makedirs(registry_path, exist_ok=True)
        os.makedirs(os.path.join(registry_path, "artifacts"), exist_ok=True)
        os.makedirs(os.path.join(registry_path, "metadata"), exist_ok=True)
        
        # Load existing registry
        self._load_registry()
        
        logger.info(f"Model Registry initialized at {registry_path}")

    def _load_registry(self):
        """Load existing registry from disk"""
        metadata_dir = os.path.join(self.registry_path, "metadata")
        if not os.path.exists(metadata_dir):
            return
        
        for filename in os.listdir(metadata_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(metadata_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    model_id = data.get('model_id')
                    if model_id:
                        self.models[model_id] = ModelMetadata(**data)
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

    def register_model(self,
                      model: Any,
                      model_name: str,
                      model_type: ModelType,
                      metrics: Dict[str, float],
                      hyperparameters: Dict[str, Any],
                      feature_names: List[str],
                      target_name: str,
                      training_samples: int,
                      validation_samples: int,
                      description: str = "",
                      tags: List[str] = None,
                      created_by: str = "system",
                      parent_model_id: Optional[str] = None) -> str:
        """
        Register a new model
        
        Args:
            model: Trained model object
            model_name: Human-readable model name
            model_type: Type of model
            metrics: Performance metrics
            hyperparameters: Model hyperparameters
            feature_names: Feature names used
            target_name: Target variable name
            training_samples: Number of training samples
            validation_samples: Number of validation samples
            description: Model description
            tags: Tags for categorization
            created_by: Creator identifier
            parent_model_id: Parent model for versioning
            
        Returns:
            Model ID
        """
        # Generate model ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_hash = self._compute_model_hash(model)
        model_id = f"{model_name.lower().replace(' ', '_')}_{timestamp}_{model_hash[:8]}"
        
        # Determine version
        if parent_model_id and parent_model_id in self.models:
            parent = self.models[parent_model_id]
            version_parts = parent.version.split('.')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            version = '.'.join(version_parts)
        else:
            version = "1.0.0"
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            model_type=model_type.value,
            version=version,
            status=ModelStatus.DEVELOPMENT.value,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=created_by,
            description=description,
            tags=tags or [],
            metrics=metrics,
            hyperparameters=hyperparameters,
            feature_names=feature_names,
            target_name=target_name,
            training_samples=training_samples,
            validation_samples=validation_samples,
            model_hash=model_hash,
            parent_model_id=parent_model_id
        )
        
        # Save model artifact
        artifact_path = self._save_artifact(model_id, model)
        
        # Register
        self.models[model_id] = metadata
        self.model_artifacts[model_id] = model
        
        # Save metadata
        self._save_metadata(metadata)
        
        # Add to version history
        version = ModelVersion(
            version=version,
            created_at=metadata.created_at,
            status=metadata.status,
            metrics=metrics,
            model_path=artifact_path,
            changelog=f"Initial version" if not parent_model_id else f"Updated from {parent_model_id}"
        )
        self.version_history[model_name].append(version)
        
        logger.info(f"Model registered: {model_id} (version {version})")
        return model_id

    def _compute_model_hash(self, model: Any) -> str:
        """Compute hash of model for identification"""
        try:
            model_bytes = pickle.dumps(model)
            return hashlib.sha256(model_bytes).hexdigest()
        except:
            return hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest()

    def _save_artifact(self, model_id: str, model: Any) -> str:
        """Save model artifact to disk"""
        artifact_path = os.path.join(self.registry_path, "artifacts", f"{model_id}.pkl")
        
        with open(artifact_path, 'wb') as f:
            pickle.dump(model, f)
        
        return artifact_path

    def _save_metadata(self, metadata: ModelMetadata):
        """Save model metadata to disk"""
        metadata_path = os.path.join(self.registry_path, "metadata", f"{metadata.model_id}.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)

    def get_model(self, model_id: str) -> Optional[Any]:
        """Get model by ID"""
        if model_id in self.model_artifacts:
            return self.model_artifacts[model_id]
        
        # Try to load from disk
        artifact_path = os.path.join(self.registry_path, "artifacts", f"{model_id}.pkl")
        if os.path.exists(artifact_path):
            with open(artifact_path, 'rb') as f:
                model = pickle.load(f)
            self.model_artifacts[model_id] = model
            return model
        
        return None

    def get_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        return self.models.get(model_id)

    def list_models(self, 
                   model_name: Optional[str] = None,
                   model_type: Optional[ModelType] = None,
                   status: Optional[ModelStatus] = None,
                   tags: Optional[List[str]] = None) -> List[ModelMetadata]:
        """List models with filters"""
        results = []
        
        for model in self.models.values():
            if model_name and model.model_name != model_name:
                continue
            if model_type and model.model_type != model_type.value:
                continue
            if status and model.status != status.value:
                continue
            if tags and not any(t in model.tags for t in tags):
                continue
            results.append(model)
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def update_model_status(self, model_id: str, status: ModelStatus) -> bool:
        """Update model status"""
        if model_id not in self.models:
            return False
        
        self.models[model_id].status = status.value
        self.models[model_id].updated_at = datetime.now().isoformat()
        self._save_metadata(self.models[model_id])
        
        logger.info(f"Model {model_id} status updated to {status.value}")
        return True

    def promote_model(self, model_id: str, to_status: ModelStatus = ModelStatus.PRODUCTION) -> bool:
        """Promote model to next stage"""
        if model_id not in self.models:
            return False
        
        return self.update_model_status(model_id, to_status)

    def delete_model(self, model_id: str) -> bool:
        """Delete model from registry"""
        if model_id not in self.models:
            return False
        
        # Delete artifact
        artifact_path = os.path.join(self.registry_path, "artifacts", f"{model_id}.pkl")
        if os.path.exists(artifact_path):
            os.remove(artifact_path)
        
        # Delete metadata
        metadata_path = os.path.join(self.registry_path, "metadata", f"{model_id}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        # Remove from memory
        del self.models[model_id]
        if model_id in self.model_artifacts:
            del self.model_artifacts[model_id]
        
        logger.info(f"Model {model_id} deleted")
        return True

    def compare_models(self, model_ids: List[str],
                      test_data: np.ndarray,
                      test_targets: np.ndarray) -> ModelComparison:
        """Compare multiple models on test data"""
        results = {}
        
        for model_id in model_ids:
            model = self.get_model(model_id)
            if model is None:
                continue
            
            try:
                predictions = model.predict(test_data)
                
                # Calculate metrics
                if len(test_targets.shape) == 1:
                    mse = float(np.mean((test_targets - predictions) ** 2))
                    mae = float(np.mean(np.abs(test_targets - predictions)))
                    r2 = float(1 - np.sum((test_targets - predictions) ** 2) / 
                              (np.sum((test_targets - np.mean(test_targets)) ** 2) + 1e-6))
                else:
                    mse = float(np.mean((test_targets - predictions) ** 2))
                    mae = float(np.mean(np.abs(test_targets - predictions)))
                    r2 = 0.0
                
                results[model_id] = {
                    'mse': mse,
                    'mae': mae,
                    'r2': r2
                }
            except Exception as e:
                logger.error(f"Failed to evaluate {model_id}: {e}")
        
        if not results:
            return ModelComparison(
                models=model_ids,
                metrics_comparison={},
                winner="",
                improvement=0,
                recommendation="No models could be evaluated"
            )
        
        # Find winner (best R2 or lowest MSE)
        if any('r2' in v and v['r2'] > 0 for v in results.values()):
            winner = max(results.keys(), key=lambda x: results[x].get('r2', 0))
            metric_used = 'r2'
        else:
            winner = min(results.keys(), key=lambda x: results[x].get('mse', float('inf')))
            metric_used = 'mse'
        
        # Calculate improvement
        sorted_results = sorted(results.items(), 
                               key=lambda x: x[1].get('r2', -float('inf')) if 'r2' in x[1] else x[1].get('mse', float('inf')),
                               reverse=True)
        
        if len(sorted_results) >= 2:
            if metric_used == 'r2':
                improvement = sorted_results[0][1]['r2'] - sorted_results[1][1]['r2']
            else:
                improvement = sorted_results[1][1]['mse'] - sorted_results[0][1]['mse']
        else:
            improvement = 0
        
        comparison = ModelComparison(
            models=list(results.keys()),
            metrics_comparison=results,
            winner=winner,
            improvement=improvement,
            recommendation=f"Model {winner} performs best with {metric_used}={results[winner][metric_used]:.4f}"
        )
        
        return comparison

    def get_version_history(self, model_name: str) -> List[ModelVersion]:
        """Get version history for a model"""
        return self.version_history.get(model_name, [])

    def export_registry(self, filepath: str) -> bool:
        """Export registry to file"""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_models': len(self.models),
                'models': [asdict(m) for m in self.models.values()],
                'version_history': {
                    name: [asdict(v) for v in versions]
                    for name, versions in self.version_history.items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Registry exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get registry summary"""
        status_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for model in self.models.values():
            status_counts[model.status] += 1
            type_counts[model.model_type] += 1
        
        return {
            'total_models': len(self.models),
            'by_status': dict(status_counts),
            'by_type': dict(type_counts),
            'total_versions': sum(len(v) for v in self.version_history.values()),
            'model_names': list(set(m.model_name for m in self.models.values()))
        }


class ModelExperiment:
    """
    Track ML experiments and their results
    """

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.experiments: Dict[str, Dict] = {}
        self.current_experiment = None

    def start_experiment(self, name: str, description: str = "",
                        tags: List[str] = None) -> str:
        """Start a new experiment"""
        experiment_id = f"exp_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.experiments[experiment_id] = {
            'experiment_id': experiment_id,
            'name': name,
            'description': description,
            'tags': tags or [],
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'status': 'running',
            'models': [],
            'metrics': {},
            'parameters': {},
            'notes': []
        }
        
        self.current_experiment = experiment_id
        logger.info(f"Experiment started: {experiment_id}")
        return experiment_id

    def log_parameters(self, params: Dict[str, Any], experiment_id: Optional[str] = None):
        """Log experiment parameters"""
        exp_id = experiment_id or self.current_experiment
        if exp_id and exp_id in self.experiments:
            self.experiments[exp_id]['parameters'].update(params)

    def log_metrics(self, metrics: Dict[str, float], experiment_id: Optional[str] = None):
        """Log experiment metrics"""
        exp_id = experiment_id or self.current_experiment
        if exp_id and exp_id in self.experiments:
            self.experiments[exp_id]['metrics'].update(metrics)

    def log_model(self, model_id: str, experiment_id: Optional[str] = None):
        """Log a model to the experiment"""
        exp_id = experiment_id or self.current_experiment
        if exp_id and exp_id in self.experiments:
            self.experiments[exp_id]['models'].append(model_id)
            
            # Update model's experiment reference
            if model_id in self.registry.models:
                self.registry.models[model_id].experiment_id = exp_id

    def log_note(self, note: str, experiment_id: Optional[str] = None):
        """Add a note to the experiment"""
        exp_id = experiment_id or self.current_experiment
        if exp_id and exp_id in self.experiments:
            self.experiments[exp_id]['notes'].append({
                'timestamp': datetime.now().isoformat(),
                'note': note
            })

    def end_experiment(self, status: str = 'completed',
                      experiment_id: Optional[str] = None) -> Dict:
        """End an experiment"""
        exp_id = experiment_id or self.current_experiment
        if exp_id and exp_id in self.experiments:
            self.experiments[exp_id]['completed_at'] = datetime.now().isoformat()
            self.experiments[exp_id]['status'] = status
            self.current_experiment = None
            
            logger.info(f"Experiment ended: {exp_id}")
            return self.experiments[exp_id]
        
        return {}

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment details"""
        return self.experiments.get(experiment_id)

    def list_experiments(self, status: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> List[Dict]:
        """List experiments with filters"""
        results = []
        
        for exp in self.experiments.values():
            if status and exp['status'] != status:
                continue
            if tags and not any(t in exp['tags'] for t in tags):
                continue
            results.append(exp)
        
        return sorted(results, key=lambda x: x['started_at'], reverse=True)

    def compare_experiments(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple experiments"""
        comparison = {
            'experiments': [],
            'metrics_comparison': {},
            'best_experiment': None
        }
        
        for exp_id in experiment_ids:
            exp = self.get_experiment(exp_id)
            if exp:
                comparison['experiments'].append({
                    'id': exp_id,
                    'name': exp['name'],
                    'status': exp['status'],
                    'models_count': len(exp['models'])
                })
                comparison['metrics_comparison'][exp_id] = exp['metrics']
        
        # Find best experiment based on primary metric
        if comparison['metrics_comparison']:
            primary_metric = 'r2_score' if any('r2_score' in m for m in comparison['metrics_comparison'].values()) else 'accuracy'
            
            best_exp = max(
                comparison['metrics_comparison'].keys(),
                key=lambda x: comparison['metrics_comparison'][x].get(primary_metric, 0)
            )
            comparison['best_experiment'] = best_exp
        
        return comparison


# Convenience function
def create_model_registry(registry_path: str = "models/registry") -> ModelRegistry:
    """Create and return a Model Registry instance"""
    return ModelRegistry(registry_path)


__all__ = [
    'ModelRegistry',
    'create_model_registry',
    'ModelExperiment',
    'ModelMetadata',
    'ModelVersion',
    'ModelComparison',
    'ModelStatus',
    'ModelType'
]
