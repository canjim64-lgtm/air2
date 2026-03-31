# AirOne v4.0 - ML Module
# Machine Learning algorithms and engines

__all__ = [
    'LocalAIDataAnalyzer',
    'AdvancedReportGenerator',
    'DeepLearningAnalyzer',
    # Enhanced ML algorithms (v4.0)
    'AutoMLSelector',
    'HyperparameterOptimizer',
    'EnsembleModelBuilder',
    'ModelPerformance',
    'ModelCategory'
]

def __getattr__(name):
    """Lazy loading of ML modules"""
    if name == 'LocalAIDataAnalyzer':
        from .advanced_ml_engine import LocalAIDataAnalyzer
        return LocalAIDataAnalyzer
    elif name == 'AdvancedReportGenerator':
        from .advanced_ml_engine import AdvancedReportGenerator
        return AdvancedReportGenerator
    elif name == 'DeepLearningAnalyzer':
        from .advanced_ml_engine import DeepLearningAnalyzer
        return DeepLearningAnalyzer
    # New v4.0 additions
    elif name == 'AutoMLSelector':
        from .enhanced_ml_algorithms import AutoMLSelector
        return AutoMLSelector
    elif name == 'HyperparameterOptimizer':
        from .enhanced_ml_algorithms import HyperparameterOptimizer
        return HyperparameterOptimizer
    elif name == 'EnsembleModelBuilder':
        from .enhanced_ml_algorithms import EnsembleModelBuilder
        return EnsembleModelBuilder
    elif name == 'ModelPerformance':
        from .enhanced_ml_algorithms import ModelPerformance
        return ModelPerformance
    elif name == 'ModelCategory':
        from .enhanced_ml_algorithms import ModelCategory
        return ModelCategory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
