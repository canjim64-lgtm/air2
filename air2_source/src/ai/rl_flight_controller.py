"""
AirOne v4.0 - Reinforcement Learning Flight Controller
Learns optimal flight control policies through trial and error
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
from collections import deque
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.linear_model import SGDRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.neural_network import MLPRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


@dataclass
class RLConfig:
    """Reinforcement Learning configuration"""
    # State space
    state_features: List[str] = None
    
    # Action space
    action_type: str = "discrete"  # discrete or continuous
    n_actions: int = 5
    
    # Learning parameters
    learning_rate: float = 0.001
    discount_factor: float = 0.99
    exploration_rate: float = 1.0
    exploration_decay: float = 0.995
    min_exploration: float = 0.01
    
    # Memory
    memory_size: int = 10000
    batch_size: int = 64
    
    # Network architecture (for DQN)
    hidden_layers: Tuple[int, ...] = (128, 64, 32)
    
    # Training
    target_update_frequency: int = 100
    learning_start_steps: int = 1000
    
    def __post_init__(self):
        if self.state_features is None:
            self.state_features = [
                'altitude', 'velocity', 'climb_rate',
                'pitch', 'roll', 'battery_percentage',
                'distance_to_target', 'error_integral'
            ]


@dataclass
class Transition:
    """Experience transition tuple"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    timestamp: str


class ReplayMemory:
    """Experience replay buffer"""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.memory: deque = deque(maxlen=capacity)
        self.position = 0

    def push(self, transition: Transition):
        """Save experience"""
        if len(self.memory) < self.capacity:
            self.memory.append(transition)
        else:
            self.memory[self.position] = transition
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> List[Transition]:
        """Sample random batch"""
        return random.sample(self.memory, batch_size)

    def __len__(self) -> int:
        return len(self.memory)

    def get_all(self) -> List[Transition]:
        """Get all transitions"""
        return list(self.memory)


class DQNNetwork:
    """
    Deep Q-Network for flight control
    Uses sklearn MLP as function approximator
    """

    def __init__(self, input_dim: int, n_actions: int, 
                 hidden_layers: Tuple[int, ...] = (128, 64, 32)):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.hidden_layers = hidden_layers
        
        self.model = None
        self.scaler = StandardScaler()
        self.is_initialized = False

    def _create_model(self) -> MLPRegressor:
        """Create neural network model"""
        return MLPRegressor(
            hidden_layer_sizes=self.hidden_layers,
            activation='relu',
            solver='adam',
            learning_rate='adaptive',
            max_iter=1,
            warm_start=True,
            random_state=42
        )

    def initialize(self, X: np.ndarray):
        """Initialize network with sample data"""
        self.scaler.fit(X)
        self.model = self._create_model()
        
        # Initialize with dummy training
        y_dummy = np.zeros((len(X), self.n_actions))
        self.model.fit(X, y_dummy)
        self.is_initialized = True

    def predict(self, state: np.ndarray) -> np.ndarray:
        """Predict Q-values for all actions"""
        if not self.is_initialized:
            return np.zeros(self.n_actions)
        
        state_scaled = self.scaler.transform(state.reshape(1, -1))
        return self.model.predict(state_scaled)[0]

    def predict_batch(self, states: np.ndarray) -> np.ndarray:
        """Predict Q-values for batch of states"""
        if not self.is_initialized:
            return np.zeros((len(states), self.n_actions))
        
        states_scaled = self.scaler.transform(states)
        return self.model.predict(states_scaled)

    def train(self, states: np.ndarray, targets: np.ndarray):
        """Train network on batch"""
        if not self.is_initialized:
            self.initialize(states)
        
        states_scaled = self.scaler.transform(states)
        
        # Multiple passes for better learning
        for _ in range(3):
            self.model.partial_fit(states_scaled, targets)


class FlightEnv:
    """
    Flight environment for RL training
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Environment parameters
        self.target_altitude = self.config.get('target_altitude', 500)
        self.max_steps = self.config.get('max_steps', 1000)
        
        # State bounds
        self.state_bounds = {
            'altitude': (0, 1000),
            'velocity': (0, 100),
            'climb_rate': (-20, 20),
            'pitch': (-45, 45),
            'roll': (-30, 30),
            'battery_percentage': (0, 100),
            'distance_to_target': (0, 1000),
            'error_integral': (-500, 500)
        }
        
        # Action space
        self.actions = ['decrease_throttle', 'hold', 'increase_throttle', 
                       'pitch_down', 'pitch_up']
        
        # State
        self.reset()

    def reset(self) -> Dict[str, float]:
        """Reset environment"""
        self.state = {
            'altitude': 0.0,
            'velocity': 0.0,
            'climb_rate': 0.0,
            'pitch': 0.0,
            'roll': 0.0,
            'battery_percentage': 100.0,
            'throttle': 0.0,
            'distance_to_target': self.target_altitude,
            'error_integral': 0.0,
            'step': 0
        }
        return self.state.copy()

    def step(self, action: int) -> Tuple[Dict[str, float], float, bool, Dict]:
        """
        Take action in environment
        
        Args:
            action: Action index
            
        Returns:
            Tuple of (next_state, reward, done, info)
        """
        self.state['step'] += 1
        
        # Apply action
        self._apply_action(action)
        
        # Update physics
        self._update_physics()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check done
        done = self._check_done()
        
        # Info
        info = {
            'altitude_error': abs(self.state['altitude'] - self.target_altitude),
            'battery_used': 100 - self.state['battery_percentage'],
            'smoothness': self._calculate_smoothness()
        }
        
        return self.state.copy(), reward, done, info

    def _apply_action(self, action: int):
        """Apply discrete action"""
        throttle_change = 0.05
        pitch_change = 2.0
        
        if action == 0:  # Decrease throttle
            self.state['throttle'] = max(0, self.state['throttle'] - throttle_change)
        elif action == 1:  # Hold
            pass
        elif action == 2:  # Increase throttle
            self.state['throttle'] = min(1, self.state['throttle'] + throttle_change)
        elif action == 3:  # Pitch down
            self.state['pitch'] = max(-45, self.state['pitch'] - pitch_change)
        elif action == 4:  # Pitch up
            self.state['pitch'] = min(45, self.state['pitch'] + pitch_change)

    def _update_physics(self):
        """Update flight physics"""
        # Simplified physics
        throttle = self.state['throttle']
        pitch = self.state['pitch']
        
        # Climb rate based on throttle and pitch
        target_climb = throttle * 30 - pitch * 0.5
        self.state['climb_rate'] += (target_climb - self.state['climb_rate']) * 0.1
        
        # Altitude
        self.state['altitude'] += self.state['climb_rate'] * 0.1
        self.state['altitude'] = max(0, self.state['altitude'])
        
        # Velocity
        self.state['velocity'] = abs(self.state['climb_rate']) + throttle * 20
        
        # Battery drain
        battery_drain = throttle * 0.1 + 0.01
        self.state['battery_percentage'] = max(0, self.state['battery_percentage'] - battery_drain)
        
        # Distance to target
        self.state['distance_to_target'] = abs(self.state['altitude'] - self.target_altitude)
        
        # Error integral
        error = self.target_altitude - self.state['altitude']
        self.state['error_integral'] += error * 0.1
        self.state['error_integral'] = max(-500, min(500, self.state['error_integral']))

    def _calculate_reward(self) -> float:
        """Calculate reward signal"""
        reward = 0.0
        
        # Altitude reward (closer to target is better)
        altitude_error = abs(self.state['altitude'] - self.target_altitude)
        reward += -altitude_error / self.target_altitude * 10
        
        # Bonus for reaching target
        if altitude_error < 10:
            reward += 5
        
        # Penalty for being on ground
        if self.state['altitude'] < 1:
            reward -= 2
        
        # Smoothness penalty
        reward -= abs(self.state['pitch']) * 0.01
        reward -= abs(self.state['climb_rate']) * 0.01
        
        # Battery efficiency
        reward -= self.state['throttle'] * 0.5
        
        # Alive reward
        reward += 0.1
        
        return reward

    def _check_done(self) -> bool:
        """Check if episode is done"""
        if self.state['step'] >= self.max_steps:
            return True
        if self.state['battery_percentage'] <= 0:
            return True
        if self.state['altitude'] > 950:  # Near target
            return True
        return False

    def _calculate_smoothness(self) -> float:
        """Calculate flight smoothness metric"""
        return 1.0 / (1.0 + abs(self.state['pitch']) + abs(self.state['climb_rate']) * 0.1)

    def get_state_vector(self) -> np.ndarray:
        """Convert state dict to vector"""
        return np.array([
            self.state['altitude'] / 1000,
            self.state['velocity'] / 100,
            self.state['climb_rate'] / 20,
            self.state['pitch'] / 45,
            self.state['roll'] / 30,
            self.state['battery_percentage'] / 100,
            self.state['distance_to_target'] / 1000,
            self.state['error_integral'] / 500
        ])


class RLFlightController:
    """
    Reinforcement Learning Flight Controller
    
    Uses Deep Q-Learning to learn optimal flight control policies
    """

    def __init__(self, config: Optional[RLConfig] = None):
        self.config = config or RLConfig()
        
        # Initialize components
        self.env = FlightEnv()
        self.memory = ReplayMemory(self.config.memory_size)
        
        # Q-Networks
        self.q_network = DQNNetwork(
            input_dim=len(self.config.state_features),
            n_actions=self.config.n_actions,
            hidden_layers=self.config.hidden_layers
        )
        self.target_network = DQNNetwork(
            input_dim=len(self.config.state_features),
            n_actions=self.config.n_actions,
            hidden_layers=self.config.hidden_layers
        )
        
        # Training state
        self.steps = 0
        self.episodes = 0
        self.total_reward = 0
        self.episode_rewards: deque = deque(maxlen=100)
        
        # Best model tracking
        self.best_avg_reward = -np.inf
        self.best_weights = None

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using epsilon-greedy policy"""
        if training and random.random() < self.config.exploration_rate:
            return random.randint(0, self.config.n_actions - 1)
        
        q_values = self.q_network.predict(state)
        return int(np.argmax(q_values))

    def store_transition(self, state: np.ndarray, action: int, 
                        reward: float, next_state: np.ndarray, done: bool):
        """Store experience transition"""
        transition = Transition(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            timestamp=datetime.now().isoformat()
        )
        self.memory.push(transition)

    def train_step(self) -> Dict[str, float]:
        """Perform one training step"""
        if len(self.memory) < self.config.batch_size:
            return {'loss': 0.0}
        
        # Sample batch
        transitions = self.memory.sample(self.config.batch_size)
        
        states = np.array([t.state for t in transitions])
        actions = np.array([t.action for t in transitions])
        rewards = np.array([t.reward for t in transitions])
        next_states = np.array([t.next_state for t in transitions])
        dones = np.array([t.done for t in transitions])
        
        # Compute target Q-values
        current_q = self.q_network.predict_batch(states)
        next_q = self.target_network.predict_batch(next_states)
        
        # Bellman update
        target_q = current_q.copy()
        for i in range(self.config.batch_size):
            target_q[i, actions[i]] = rewards[i] + \
                (1 - dones[i]) * self.config.discount_factor * np.max(next_q[i])
        
        # Train
        self.q_network.train(states, target_q)
        
        # Calculate loss
        loss = float(np.mean((current_q - target_q) ** 2))
        
        # Update target network periodically
        if self.steps % self.config.target_update_frequency == 0:
            self._update_target_network()
        
        # Decay exploration
        self.config.exploration_rate = max(
            self.config.min_exploration,
            self.config.exploration_rate * self.config.exploration_decay
        )
        
        return {'loss': loss}

    def _update_target_network(self):
        """Update target network weights"""
        # Copy Q-network to target network
        if self.q_network.is_initialized:
            self.target_network.model = self.q_network.model
            self.target_network.scaler = self.q_network.scaler
            self.target_network.is_initialized = True

    def train_episode(self, max_steps: int = 500) -> Dict[str, Any]:
        """Train for one episode"""
        state = self.env.reset()
        state_vec = self.env.get_state_vector()
        
        episode_reward = 0
        episode_loss = 0
        n_steps = 0
        
        for step in range(max_steps):
            # Select action
            action = self.select_action(state_vec, training=True)
            
            # Take action
            next_state, reward, done, info = self.env.step(action)
            next_state_vec = self.env.get_state_vector()
            
            # Store transition
            self.store_transition(state_vec, action, reward, next_state_vec, done)
            
            # Train
            if self.steps > self.config.learning_start_steps:
                train_result = self.train_step()
                episode_loss += train_result.get('loss', 0)
            
            # Update counters
            state_vec = next_state_vec
            episode_reward += reward
            n_steps += 1
            self.steps += 1
            
            if done:
                break
        
        # Update episode counters
        self.episodes += 1
        self.total_reward += episode_reward
        self.episode_rewards.append(episode_reward)
        
        # Track best model
        avg_reward = np.mean(self.episode_rewards)
        if avg_reward > self.best_avg_reward:
            self.best_avg_reward = avg_reward
        
        return {
            'episode': self.episodes,
            'reward': episode_reward,
            'avg_reward': avg_reward,
            'steps': n_steps,
            'loss': episode_loss / n_steps if n_steps > 0 else 0,
            'exploration': self.config.exploration_rate,
            'best_avg_reward': self.best_avg_reward
        }

    def train(self, n_episodes: int = 100, 
              verbose: bool = True) -> List[Dict[str, Any]]:
        """
        Train for multiple episodes
        
        Args:
            n_episodes: Number of episodes to train
            verbose: Print progress
            
        Returns:
            Training history
        """
        logger.info(f"Starting RL training for {n_episodes} episodes...")
        
        history = []
        
        for episode in range(n_episodes):
            episode_result = self.train_episode()
            history.append(episode_result)
            
            if verbose and (episode + 1) % 10 == 0:
                logger.info(
                    f"Episode {episode + 1}/{n_episodes}: "
                    f"reward={episode_result['reward']:.2f}, "
                    f"avg={episode_result['avg_reward']:.2f}, "
                    f"loss={episode_result['loss']:.4f}, "
                    f"exploration={episode_result['exploration']:.3f}"
                )
        
        logger.info(f"Training complete. Best avg reward: {self.best_avg_reward:.2f}")
        return history

    def get_control_action(self, state: Dict[str, Any]) -> int:
        """
        Get control action for current state (inference mode)
        
        Args:
            state: Current flight state
            
        Returns:
            Action index
        """
        # Convert state to vector
        state_vec = np.array([
            state.get('altitude', 0) / 1000,
            state.get('velocity', 0) / 100,
            state.get('climb_rate', 0) / 20,
            state.get('pitch', 0) / 45,
            state.get('roll', 0) / 30,
            state.get('battery_percentage', 100) / 100,
            state.get('distance_to_target', 500) / 1000,
            state.get('error_integral', 0) / 500
        ])
        
        # Get Q-values
        q_values = self.q_network.predict(state_vec)
        
        # Select best action
        return int(np.argmax(q_values))

    def get_action_name(self, action: int) -> str:
        """Get action name from index"""
        if 0 <= action < len(self.env.actions):
            return self.env.actions[action]
        return 'unknown'

    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            'total_episodes': self.episodes,
            'total_steps': self.steps,
            'total_reward': self.total_reward,
            'avg_episode_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'best_avg_reward': self.best_avg_reward,
            'current_exploration': self.config.exploration_rate,
            'memory_size': len(self.memory),
            'q_network_initialized': self.q_network.is_initialized
        }

    def save_policy(self, filepath: str) -> bool:
        """Save learned policy"""
        try:
            import pickle
            policy_data = {
                'q_network_model': self.q_network.model,
                'q_network_scaler': self.q_network.scaler,
                'config': asdict(self.config),
                'training_stats': self.get_training_stats()
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(policy_data, f)
            
            logger.info(f"Policy saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save policy: {e}")
            return False

    def load_policy(self, filepath: str) -> bool:
        """Load learned policy"""
        try:
            import pickle
            with open(filepath, 'rb') as f:
                policy_data = pickle.load(f)
            
            self.q_network.model = policy_data['q_network_model']
            self.q_network.scaler = policy_data['q_network_scaler']
            self.q_network.is_initialized = True
            
            logger.info(f"Policy loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            return False


# Convenience function
def create_rl_flight_controller(config: Optional[RLConfig] = None) -> RLFlightController:
    """Create and return an RL Flight Controller instance"""
    return RLFlightController(config)


__all__ = [
    'RLFlightController',
    'create_rl_flight_controller',
    'RLConfig',
    'FlightEnv',
    'DQNNetwork',
    'ReplayMemory',
    'Transition'
]
