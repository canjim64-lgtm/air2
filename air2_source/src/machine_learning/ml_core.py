"""
Machine Learning Module - Full Implementation
Training, inference, and model management for CanSat AI
"""

import numpy as np
import pickle
import json
from typing import Dict, List, Tuple, Any
from collections import deque


class LinearRegression:
    """Linear regression with gradient descent"""
    
    def __init__(self, learning_rate: float = 0.01, iterations: int = 1000):
        self.lr = learning_rate
        self.iterations = iterations
        self.weights = None
        self.bias = None
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train the model"""
        n_samples, n_features = X.shape
        
        self.weights = np.zeros(n_features)
        self.bias = 0
        
        for _ in range(self.iterations):
            y_pred = np.dot(X, self.weights) + self.bias
            
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y))
            db = (1 / n_samples) * np.sum(y_pred - y)
            
            self.weights -= self.lr * dw
            self.bias -= self.lr * db
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict"""
        return np.dot(X, self.weights) + self.bias
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """R2 score"""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)


class RandomForest:
    """Random Forest classifier (simplified)"""
    
    def __init__(self, n_trees: int = 10, max_depth: int = 5):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.trees = []
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train forest"""
        self.trees = []
        
        for _ in range(self.n_trees):
            # Bootstrap sample
            indices = np.random.choice(len(X), len(X), replace=True)
            X_boot = X[indices]
            y_boot = y[indices]
            
            # Train simple tree
            tree = self._build_tree(X_boot, y_boot, 0)
            self.trees.append(tree)
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> Dict:
        """Build decision tree"""
        if depth >= self.max_depth or len(np.unique(y)) == 1:
            return {'class': np.bincount(y).argmax()}
        
        # Find best split
        best_gain = 0
        best_feature = 0
        best_threshold = 0
        
        for feature in range(X.shape[1]):
            thresholds = np.unique(X[:, feature])[:10]
            for threshold in thresholds:
                left = X[:, feature] <= threshold
                right = ~left
                
                if np.sum(left) < 1 or np.sum(right) < 1:
                    continue
                
                gain = self._information_gain(y, y[left], y[right])
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold
        
        if best_gain == 0:
            return {'class': np.bincount(y).argmax()}
        
        left = X[:, best_feature] <= best_threshold
        right = ~left
        
        return {
            'feature': best_feature,
            'threshold': best_threshold,
            'left': self._build_tree(X[left], y[left], depth + 1),
            'right': self._build_tree(X[right], y[right], depth + 1)
        }
    
    def _information_gain(self, y: np.ndarray, y_left: np.ndarray, y_right: np.ndarray) -> float:
        """Calculate information gain"""
        def entropy(y):
            if len(y) == 0:
                return 0
            probs = np.bincount(y) / len(y)
            return -np.sum(probs * np.log2(probs + 1e-10))
        
        parent_entropy = entropy(y)
        n = len(y)
        
        if n == 0:
            return 0
        
        left_entropy = entropy(y_left) * len(y_left) / n
        right_entropy = entropy(y_right) * len(y_right) / n
        
        return parent_entropy - left_entropy - right_entropy
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict"""
        predictions = np.array([self._predict_tree(x, tree) for tree in self.trees for x in X])
        predictions = predictions.reshape(len(X), self.n_trees)
        return np.array([np.bincount(row).argmax() for row in predictions])
    
    def _predict_tree(self, x: np.ndarray, tree: Dict) -> int:
        """Predict with tree"""
        if 'class' in tree:
            return tree['class']
        
        if x[tree['feature']] <= tree['threshold']:
            return self._predict_tree(x, tree['left'])
        else:
            return self._predict_tree(x, tree['right'])


class MLP:
    """Multi-Layer Perceptron"""
    
    def __init__(self, layers: List[int], learning_rate: float = 0.01):
        self.layers = layers
        self.lr = learning_rate
        self.weights = []
        self.biases = []
        
        # Initialize weights
        for i in range(len(layers) - 1):
            self.weights.append(np.random.randn(layers[i], layers[i+1]) * 0.1)
            self.biases.append(np.zeros(layers[i+1]))
    
    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 100):
        """Train MLP"""
        
        for _ in range(epochs):
            # Forward pass
            activations = [X]
            for i in range(len(self.weights)):
                z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
                a = self._relu(z)
                activations.append(a)
            
            # Backward pass
            delta = activations[-1] - y
            
            for i in range(len(self.weights) - 1, -1, -1):
                dw = np.dot(activations[i].T, delta) / len(X)
                db = np.mean(delta, axis=0)
                
                self.weights[i] -= self.lr * dw
                self.biases[i] -= self.lr * db
                
                if i > 0:
                    delta = np.dot(delta, self.weights[i].T) * self._relu_derivative(activations[i])
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)
    
    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict"""
        a = X
        for i in range(len(self.weights)):
            a = self._relu(np.dot(a, self.weights[i]) + self.biases[i])
        return a


class LSTMNetwork:
    """LSTM for time series prediction"""
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize weights
        self.Wf = np.random.randn(input_size + hidden_size, hidden_size) * 0.1
        self.Wi = np.random.randn(input_size + hidden_size, hidden_size) * 0.1
        self.Wc = np.random.randn(input_size + hidden_size, hidden_size) * 0.1
        self.Wo = np.random.randn(input_size + hidden_size, hidden_size) * 0.1
        self.Wy = np.random.randn(hidden_size, output_size) * 0.1
        
        self.bf = np.zeros(hidden_size)
        self.bi = np.zeros(hidden_size)
        self.bc = np.zeros(hidden_size)
        self.bo = np.zeros(hidden_size)
        self.by = np.zeros(output_size)
    
    def forward(self, x_seq: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Forward pass through LSTM"""
        
        T = len(x_seq)
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)
        
        outputs = []
        
        for t in range(T):
            x = x_seq[t]
            combined = np.concatenate([x, h])
            
            # Gates
            f = self._sigmoid(np.dot(combined, self.Wf) + self.bf)
            i = self._sigmoid(np.dot(combined, self.Wi) + self.bi)
            c_tilde = np.tanh(np.dot(combined, self.Wc) + self.bc)
            o = self._sigmoid(np.dot(combined, self.Wo) + self.bo)
            
            # Cell state
            c = f * c + i * c_tilde
            h = o * np.tanh(c)
            
            # Output
            y = np.dot(h, self.Wy) + self.by
            outputs.append(y)
        
        return outputs[-1], {'h': h, 'c': c}
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict next values"""
        _, state = self.forward(X)
        return np.dot(state['h'], self.Wy) + self.by


class KMeans:
    """K-Means clustering"""
    
    def __init__(self, n_clusters: int = 3, max_iter: int = 100):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.centroids = None
    
    def fit(self, X: np.ndarray):
        """Fit K-Means"""
        
        # Random initialization
        indices = np.random.choice(len(X), self.n_clusters, replace=False)
        self.centroids = X[indices].copy()
        
        for _ in range(self.max_iter):
            # Assign clusters
            distances = np.zeros((len(X), self.n_clusters))
            for k in range(self.n_clusters):
                distances[:, k] = np.linalg.norm(X - self.centroids[k], axis=1)
            
            labels = np.argmin(distances, axis=1)
            
            # Update centroids
            new_centroids = np.zeros_like(self.centroids)
            for k in range(self.n_clusters):
                if np.sum(labels == k) > 0:
                    new_centroids[k] = X[labels == k].mean(axis=0)
                else:
                    new_centroids[k] = self.centroids[k]
            
            if np.allclose(self.centroids, new_centroids):
                break
            
            self.centroids = new_centroids
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels"""
        distances = np.zeros((len(X), self.n_clusters))
        for k in range(self.n_clusters):
            distances[:, k] = np.linalg.norm(X - self.centroids[k], axis=1)
        return np.argmin(distances, axis=1)


class PCA:
    """Principal Component Analysis"""
    
    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self.components = None
        self.mean = None
        self.explained_variance = None
    
    def fit(self, X: np.ndarray):
        """Fit PCA"""
        
        # Center data
        self.mean = np.mean(X, axis=0)
        X_centered = X - self.mean
        
        # SVD
        U, S, Vt = np.linalg.svd(X_centered)
        
        self.components = Vt[:self.n_components]
        self.explained_variance = S[:self.n_components] ** 2 / len(X)
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform to principal components"""
        return np.dot(X - self.mean, self.components.T)
    
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform"""
        return np.dot(X, self.components) + self.mean


class StandardScaler:
    """StandardScaler for normalization"""
    
    def __init__(self):
        self.mean = None
        self.std = None
    
    def fit(self, X: np.ndarray):
        """Fit scaler"""
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0) + 1e-10
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform"""
        return (X - self.mean) / self.std
    
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform"""
        return X * self.std + self.mean


class ModelSaver:
    """Save and load trained models"""
    
    @staticmethod
    def save(model: Any, path: str):
        """Save model to file"""
        with open(path, 'wb') as f:
            pickle.dump(model, f)
    
    @staticmethod
    def load(path: str) -> Any:
        """Load model from file"""
        with open(path, 'rb') as f:
            return pickle.load(f)


class CrossValidator:
    """K-fold cross validation"""
    
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits
    
    def validate(self, model_class, X: np.ndarray, y: np.ndarray, **kwargs):
        """Run cross validation"""
        
        indices = np.arange(len(X))
        np.random.shuffle(indices)
        
        fold_size = len(X) // self.n_splits
        scores = []
        
        for i in range(self.n_splits):
            test_indices = indices[i * fold_size:(i + 1) * fold_size]
            train_indices = np.concatenate([indices[:i * fold_size], indices[(i + 1) * fold_size:]])
            
            X_train, X_test = X[train_indices], X[test_indices]
            y_train, y_test = y[train_indices], y[test_indices]
            
            model = model_class(**kwargs)
            model.fit(X_train, y_train)
            
            if hasattr(model, 'score'):
                score = model.score(X_test, y_test)
                scores.append(score)
        
        return {
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'scores': scores
        }


# Example
if __name__ == "__main__":
    # Test linear regression
    X = np.random.randn(100, 3)
    y = 3 * X[:, 0] + 2 * X[:, 1] + 5
    
    lr = LinearRegression()
    lr.fit(X, y)
    print(f"Linear Regression R2: {lr.score(X, y):.3f}")
    
    # Test K-Means
    X_clusters = np.random.randn(50, 2)
    X_clusters[:25] += 5
    
    km = KMeans(n_clusters=2)
    km.fit(X_clusters)
    labels = km.predict(X_clusters)
    print(f"K-Means clusters: {np.unique(labels)}")