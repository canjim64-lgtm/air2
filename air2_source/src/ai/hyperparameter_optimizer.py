"""
AirOne v4.0 - Advanced Hyperparameter Optimization
Bayesian optimization, evolutionary search, and multi-fidelity optimization
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, RBF, ConstantKernel as C
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


@dataclass
class HyperparameterSpace:
    """Definition of hyperparameter search space"""
    name: str
    param_type: str  # continuous, integer, categorical
    low: Optional[float] = None
    high: Optional[float] = None
    values: Optional[List[Any]] = None
    log_scale: bool = False
    default: Optional[Any] = None


@dataclass
class TrialResult:
    """Result of a single hyperparameter trial"""
    trial_id: int
    params: Dict[str, Any]
    score: float
    duration_seconds: float
    status: str  # completed, failed, pruned
    timestamp: str


@dataclass
class OptimizationResult:
    """Final optimization result"""
    best_params: Dict[str, Any]
    best_score: float
    total_trials: int
    total_duration: float
    trials: List[TrialResult]
    convergence_history: List[float]
    optimization_method: str


class BayesianOptimizer:
    """
    Bayesian Optimization using Gaussian Processes
    """

    def __init__(self, param_space: Dict[str, HyperparameterSpace],
                 n_initial_points: int = 5,
                 acquisition_function: str = 'ei'):
        self.param_space = param_space
        self.n_initial_points = n_initial_points
        self.acquisition_function = acquisition_function
        
        self.gp_model = None
        self.X_sample = []
        self.y_sample = []
        self.n_calls = 0
        
        # GP kernel
        self.kernel = C(1.0, (1e-3, 1e3)) * Matern(length_scale_bounds=(1e-2, 1e2))

    def _sample_random_params(self) -> Dict[str, Any]:
        """Sample random parameters from search space"""
        params = {}
        for name, space in self.param_space.items():
            if space.param_type == 'continuous':
                if space.log_scale:
                    params[name] = np.exp(np.random.uniform(
                        np.log(space.low), np.log(space.high)))
                else:
                    params[name] = np.random.uniform(space.low, space.high)
            elif space.param_type == 'integer':
                params[name] = np.random.randint(int(space.low), int(space.high) + 1)
            elif space.param_type == 'categorical':
                params[name] = random.choice(space.values)
        return params

    def _params_to_vector(self, params: Dict[str, Any]) -> np.ndarray:
        """Convert params dict to vector"""
        vector = []
        for name, space in self.param_space.items():
            val = params[name]
            if space.param_type in ['continuous', 'integer']:
                if space.log_scale:
                    vector.append(np.log(val))
                else:
                    vector.append(val)
            elif space.param_type == 'categorical':
                idx = space.values.index(val) if val in space.values else 0
                vector.append(idx / len(space.values))
        return np.array(vector).reshape(1, -1)

    def _vector_to_params(self, vector: np.ndarray) -> Dict[str, Any]:
        """Convert vector to params dict"""
        params = {}
        idx = 0
        for name, space in self.param_space.items():
            if space.param_type == 'continuous':
                val = vector[0, idx]
                if space.log_scale:
                    val = np.exp(val)
                params[name] = np.clip(val, space.low, space.high)
                idx += 1
            elif space.param_type == 'integer':
                val = int(np.round(vector[0, idx]))
                params[name] = int(np.clip(val, space.low, space.high))
                idx += 1
            elif space.param_type == 'categorical':
                cat_idx = int(np.round(vector[0, idx] * len(space.values)))
                cat_idx = int(np.clip(cat_idx, 0, len(space.values) - 1))
                params[name] = space.values[cat_idx]
                idx += 1
        return params

    def _acquisition(self, X: np.ndarray) -> np.ndarray:
        """Calculate acquisition function"""
        if self.gp_model is None:
            return np.zeros(len(X))
        
        mu, sigma = self.gp_model.predict(X, return_std=True)
        
        if self.acquisition_function == 'ei':
            # Expected Improvement
            f_min = np.min(self.y_sample)
            with np.errstate(divide='ignore'):
                z = (f_min - mu) / sigma
                ei = (f_min - mu) * self._norm_cdf(z) + sigma * self._norm_pdf(z)
            return ei
        elif self.acquisition_function == 'ucb':
            # Upper Confidence Bound
            kappa = 2.576  # 99% confidence
            return mu + kappa * sigma
        elif self.acquisition_function == 'poi':
            # Probability of Improvement
            f_min = np.min(self.y_sample)
            with np.errstate(divide='ignore'):
                z = (f_min - mu) / sigma
                poi = self._norm_cdf(z)
            return poi
        else:
            return np.zeros(len(X))

    def _norm_cdf(self, x: np.ndarray) -> np.ndarray:
        """Standard normal CDF"""
        return 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def _norm_pdf(self, x: np.ndarray) -> np.ndarray:
        """Standard normal PDF"""
        return np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi)

    def suggest(self) -> Dict[str, Any]:
        """Suggest next parameters to evaluate"""
        if len(self.X_sample) < self.n_initial_points:
            return self._sample_random_params()
        
        # Fit GP model
        X = np.vstack(self.X_sample)
        y = np.array(self.y_sample)
        
        self.gp_model = GaussianProcessRegressor(
            kernel=self.kernel,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=42
        )
        self.gp_model.fit(X, y)
        
        # Optimize acquisition function
        from scipy.optimize import minimize
        
        def neg_acquisition(x_flat):
            x = x_flat.reshape(1, -1)
            return -self._acquisition(x)[0]
        
        # Multiple restarts
        best_x = None
        best_acq = -np.inf
        
        for _ in range(10):
            x0 = np.random.uniform(-1, 1, len(self.param_space))
            res = minimize(neg_acquisition, x0, method='L-BFGS-B',
                          bounds=[(-1, 1)] * len(self.param_space))
            if -res.fun > best_acq:
                best_acq = -res.fun
                best_x = res.x
        
        return self._vector_to_params(best_x.reshape(1, -1))

    def tell(self, params: Dict[str, Any], score: float):
        """Record evaluation result"""
        self.X_sample.append(self._params_to_vector(params))
        self.y_sample.append(score)
        self.n_calls += 1

    def optimize(self, objective: Callable, n_calls: int = 50,
                verbose: bool = True) -> OptimizationResult:
        """
        Run Bayesian optimization
        
        Args:
            objective: Function to minimize
            n_calls: Number of optimization iterations
            verbose: Print progress
            
        Returns:
            OptimizationResult
        """
        logger.info(f"Starting Bayesian Optimization for {n_calls} iterations...")
        
        trials = []
        convergence_history = []
        start_time = datetime.now()
        
        for i in range(n_calls):
            trial_start = datetime.now()
            
            # Suggest parameters
            params = self.suggest()
            
            try:
                # Evaluate objective
                score = objective(params)
                status = 'completed'
            except Exception as e:
                logger.error(f"Trial {i+1} failed: {e}")
                score = float('inf')
                status = 'failed'
            
            # Record result
            self.tell(params, score)
            
            trial_duration = (datetime.now() - trial_start).total_seconds()
            
            trial = TrialResult(
                trial_id=i + 1,
                params=params,
                score=score,
                duration_seconds=trial_duration,
                status=status,
                timestamp=datetime.now().isoformat()
            )
            trials.append(trial)
            convergence_history.append(np.min(self.y_sample))
            
            if verbose and (i + 1) % 10 == 0:
                logger.info(
                    f"Iteration {i+1}/{n_calls}: "
                    f"best_score={np.min(self.y_sample):.4f}"
                )
        
        # Get best result
        best_idx = np.argmin(self.y_sample)
        best_params = self._vector_to_params(np.array(self.X_sample[best_idx]))
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        return OptimizationResult(
            best_params=best_params,
            best_score=float(np.min(self.y_sample)),
            total_trials=len(trials),
            total_duration=total_duration,
            trials=trials,
            convergence_history=convergence_history,
            optimization_method='bayesian'
        )


class EvolutionaryOptimizer:
    """
    Evolutionary/Hyperparameter optimization using genetic algorithms
    """

    def __init__(self, param_space: Dict[str, HyperparameterSpace],
                 population_size: int = 20,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elitism_rate: float = 0.1):
        self.param_space = param_space
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_rate = elitism_rate
        
        self.population = []
        self.fitness = []
        self.generation = 0

    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        for _ in range(self.population_size):
            individual = {}
            for name, space in self.param_space.items():
                if space.param_type == 'continuous':
                    if space.log_scale:
                        individual[name] = np.exp(np.random.uniform(
                            np.log(space.low), np.log(space.high)))
                    else:
                        individual[name] = np.random.uniform(space.low, space.high)
                elif space.param_type == 'integer':
                    individual[name] = np.random.randint(int(space.low), int(space.high) + 1)
                elif space.param_type == 'categorical':
                    individual[name] = random.choice(space.values)
            self.population.append(individual)
        self.fitness = []
        self.generation = 0

    def _evaluate_fitness(self, objective: Callable) -> List[float]:
        """Evaluate fitness of population"""
        self.fitness = []
        for individual in self.population:
            try:
                score = objective(individual)
                self.fitness.append(score)
            except:
                self.fitness.append(float('inf'))
        return self.fitness

    def _selection(self) -> List[Dict]:
        """Tournament selection"""
        selected = []
        tournament_size = 3
        
        for _ in range(self.population_size):
            contestants = random.sample(list(zip(self.population, self.fitness)), 
                                        tournament_size)
            winner = min(contestants, key=lambda x: x[1])[0]
            selected.append(winner.copy())
        
        return selected

    def _crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """Single-point crossover"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1, child2 = {}, {}
        keys = list(self.param_space.keys())
        crossover_point = random.randint(1, len(keys) - 1)
        
        for i, key in enumerate(keys):
            space = self.param_space[key]
            if i < crossover_point:
                child1[key] = parent1[key]
                child2[key] = parent2[key]
            else:
                child1[key] = parent2[key]
                child2[key] = parent1[key]
        
        return child1, child2

    def _mutate(self, individual: Dict) -> Dict:
        """Mutate individual"""
        mutated = individual.copy()
        
        for name, space in self.param_space.items():
            if random.random() < self.mutation_rate:
                if space.param_type == 'continuous':
                    # Gaussian mutation
                    std = (space.high - space.low) * 0.1
                    mutated[name] += np.random.normal(0, std)
                    if space.log_scale:
                        mutated[name] = np.clip(mutated[name], space.low, space.high)
                    else:
                        mutated[name] = np.clip(mutated[name], space.low, space.high)
                elif space.param_type == 'integer':
                    mutated[name] += np.random.randint(-1, 2)
                    mutated[name] = int(np.clip(mutated[name], space.low, space.high))
                elif space.param_type == 'categorical':
                    mutated[name] = random.choice(space.values)
        
        return mutated

    def optimize(self, objective: Callable, n_generations: int = 50,
                verbose: bool = True) -> OptimizationResult:
        """Run evolutionary optimization"""
        logger.info(f"Starting Evolutionary Optimization for {n_generations} generations...")
        
        self._initialize_population()
        
        trials = []
        convergence_history = []
        start_time = datetime.now()
        trial_id = 0
        
        for gen in range(n_generations):
            # Evaluate fitness
            self._evaluate_fitness(objective)
            
            # Record trials
            for i, (ind, fit) in enumerate(zip(self.population, self.fitness)):
                trial_id += 1
                trials.append(TrialResult(
                    trial_id=trial_id,
                    params=ind.copy(),
                    score=fit,
                    duration_seconds=0,
                    status='completed',
                    timestamp=datetime.now().isoformat()
                ))
            
            best_score = np.min(self.fitness)
            convergence_history.append(best_score)
            
            if verbose and (gen + 1) % 10 == 0:
                logger.info(f"Generation {gen+1}/{n_generations}: best_score={best_score:.4f}")
            
            # Create next generation
            n_elites = int(self.population_size * self.elitism_rate)
            
            # Elitism
            elite_indices = np.argsort(self.fitness)[:n_elites]
            new_population = [self.population[i].copy() for i in elite_indices]
            
            # Selection
            selected = self._selection()
            
            # Crossover and mutation
            while len(new_population) < self.population_size:
                parent1, parent2 = random.sample(selected, 2)
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                new_population.extend([child1, child2])
            
            self.population = new_population[:self.population_size]
            self.generation += 1
        
        # Get best result
        self._evaluate_fitness(objective)
        best_idx = np.argmin(self.fitness)
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        return OptimizationResult(
            best_params=self.population[best_idx],
            best_score=float(self.fitness[best_idx]),
            total_trials=trial_id,
            total_duration=total_duration,
            trials=trials,
            convergence_history=convergence_history,
            optimization_method='evolutionary'
        )


class HyperparameterOptimizer:
    """
    Unified hyperparameter optimization interface
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.optimization_history: List[OptimizationResult] = []

    def optimize(self, objective: Callable,
                param_space: Dict[str, Dict],
                method: str = 'bayesian',
                n_iterations: int = 50,
                verbose: bool = True) -> OptimizationResult:
        """
        Optimize hyperparameters
        
        Args:
            objective: Function to minimize
            param_space: Parameter space definition
            method: Optimization method
            n_iterations: Number of iterations
            verbose: Print progress
            
        Returns:
            OptimizationResult
        """
        # Convert param_space to HyperparameterSpace objects
        space = {}
        for name, config in param_space.items():
            space[name] = HyperparameterSpace(
                name=name,
                param_type=config.get('type', 'continuous'),
                low=config.get('low'),
                high=config.get('high'),
                values=config.get('values'),
                log_scale=config.get('log_scale', False),
                default=config.get('default')
            )
        
        # Select optimizer
        if method == 'bayesian':
            optimizer = BayesianOptimizer(space)
        elif method == 'evolutionary':
            optimizer = EvolutionaryOptimizer(space)
        elif method == 'random':
            optimizer = RandomSearchOptimizer(space)
        else:
            optimizer = BayesianOptimizer(space)
        
        # Run optimization
        result = optimizer.optimize(objective, n_iterations, verbose)
        self.optimization_history.append(result)
        
        return result


class RandomSearchOptimizer:
    """Random search optimizer"""

    def __init__(self, param_space: Dict[str, HyperparameterSpace]):
        self.param_space = param_space

    def _sample_params(self) -> Dict[str, Any]:
        """Sample random parameters"""
        params = {}
        for name, space in self.param_space.items():
            if space.param_type == 'continuous':
                if space.log_scale:
                    params[name] = np.exp(np.random.uniform(
                        np.log(space.low), np.log(space.high)))
                else:
                    params[name] = np.random.uniform(space.low, space.high)
            elif space.param_type == 'integer':
                params[name] = np.random.randint(int(space.low), int(space.high) + 1)
            elif space.param_type == 'categorical':
                params[name] = random.choice(space.values)
        return params

    def optimize(self, objective: Callable, n_calls: int = 50,
                verbose: bool = True) -> OptimizationResult:
        """Run random search"""
        logger.info(f"Starting Random Search for {n_calls} iterations...")
        
        trials = []
        convergence_history = []
        best_score = float('inf')
        best_params = None
        start_time = datetime.now()
        
        for i in range(n_calls):
            trial_start = datetime.now()
            params = self._sample_params()
            
            try:
                score = objective(params)
                status = 'completed'
            except:
                score = float('inf')
                status = 'failed'
            
            if score < best_score:
                best_score = score
                best_params = params
            
            convergence_history.append(best_score)
            
            trials.append(TrialResult(
                trial_id=i + 1,
                params=params,
                score=score,
                duration_seconds=(datetime.now() - trial_start).total_seconds(),
                status=status,
                timestamp=datetime.now().isoformat()
            ))
            
            if verbose and (i + 1) % 10 == 0:
                logger.info(f"Iteration {i+1}/{n_calls}: best_score={best_score:.4f}")
        
        return OptimizationResult(
            best_params=best_params or {},
            best_score=best_score,
            total_trials=len(trials),
            total_duration=(datetime.now() - start_time).total_seconds(),
            trials=trials,
            convergence_history=convergence_history,
            optimization_method='random'
        )


# Convenience function
def create_hyperparameter_optimizer(config: Optional[Dict] = None) -> HyperparameterOptimizer:
    """Create and return a Hyperparameter Optimizer instance"""
    return HyperparameterOptimizer(config)


__all__ = [
    'HyperparameterOptimizer',
    'create_hyperparameter_optimizer',
    'BayesianOptimizer',
    'EvolutionaryOptimizer',
    'RandomSearchOptimizer',
    'HyperparameterSpace',
    'TrialResult',
    'OptimizationResult'
]
