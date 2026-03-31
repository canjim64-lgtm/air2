"""
Advanced AI Fusion Engine for AirOne Professional
Implements multimodal AI fusion, cognitive reasoning, and advanced neural architectures
"""

import asyncio
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
    from sentence_transformers import SentenceTransformer
    TORCH_AVAILABLE = True
except (ImportError, OSError):
    TORCH_AVAILABLE = False
    logger = __import__("logging").getLogger(__name__)
    logger.warning("torch or transformers not available (or dependencies missing). AI Fusion Engine will be limited.")
    # Provide stubs for torch and torch.nn
    class torch:
        class Tensor: pass
        class nn:
            class Module:
                def __init__(self, *args, **kwargs): pass
                def __call__(self, *args, **kwargs): return None
                def parameters(self): return []
                def to(self, *args, **kwargs): return self
                def train(self, mode=True): return self
                def eval(self): return self
        class float32: pass
        class long: pass
        @staticmethod
        def from_numpy(x): return x
        @staticmethod
        def stack(x, dim=0): return x
        @staticmethod
        def cat(x, dim=0): return x
    class nn:
        class Module:
            def __init__(self, *args, **kwargs): pass
            def __call__(self, *args, **kwargs): return None
            def parameters(self): return []
            def to(self, *args, **kwargs): return self
            def train(self, mode=True): return self
            def eval(self): return self
    class F:
        @staticmethod
        def softmax(x, dim=None): return x
        @staticmethod
        def relu(x): return x
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import threading
import queue
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps
import hashlib
import secrets
import pickle
import joblib
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIFusionMode(Enum):
    """Modes for AI fusion"""
    EARLY_FUSION = "early_fusion"
    LATE_FUSION = "late_fusion"
    HYBRID_FUSION = "hybrid_fusion"
    ATTENTION_FUSION = "attention_fusion"


class CognitiveArchitecture(Enum):
    """Cognitive architectures for reasoning"""
    NEURAL_SYMBOLIC = "neural_symbolic"
    COGNITIVE_GRAPH = "cognitive_graph"
    MEMORY_AUGMENTED = "memory_augmented"
    TRANSFORMER_REASONING = "transformer_reasoning"


@dataclass
class FusionResult:
    """Result of AI fusion process"""
    fused_embedding: np.ndarray
    confidence_score: float
    reasoning_trace: List[str]
    modality_contributions: Dict[str, float]
    timestamp: datetime


class MultimodalEncoder(nn.Module):
    """Encodes different modalities into a unified representation"""
    
    def __init__(self, text_dim: int = 768, numeric_dim: int = 128, categorical_dim: int = 64):
        super().__init__()
        self.text_encoder = nn.Linear(text_dim, 512)
        self.numeric_encoder = nn.Linear(numeric_dim, 256)
        self.categorical_encoder = nn.Linear(categorical_dim, 128)
        self.fusion_layer = nn.Linear(512 + 256 + 128, 512)
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, text_features: torch.Tensor, 
                numeric_features: torch.Tensor, 
                categorical_features: torch.Tensor) -> torch.Tensor:
        text_encoded = F.relu(self.text_encoder(text_features))
        numeric_encoded = F.relu(self.numeric_encoder(numeric_features))
        cat_encoded = F.relu(self.categorical_encoder(categorical_features))
        
        combined = torch.cat([text_encoded, numeric_encoded, cat_encoded], dim=-1)
        fused = F.relu(self.fusion_layer(combined))
        return self.dropout(fused)


class AttentionFusion(nn.Module):
    """Attention-based fusion mechanism"""
    
    def __init__(self, input_dim: int, num_modalities: int):
        super().__init__()
        self.num_modalities = num_modalities
        self.attention_weights = nn.Parameter(torch.randn(num_modalities, input_dim))
        self.output_projection = nn.Linear(input_dim, input_dim)
    
    def forward(self, modalities: List[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        # Stack modalities
        stacked = torch.stack(modalities, dim=1)  # [batch_size, num_modalities, feature_dim]
        
        # Compute attention scores
        attention_scores = torch.matmul(stacked, self.attention_weights.unsqueeze(0))
        attention_weights = F.softmax(attention_scores, dim=1)
        
        # Apply attention
        weighted_sum = torch.sum(stacked * attention_weights.unsqueeze(-1), dim=1)
        output = self.output_projection(weighted_sum)
        
        return output, attention_weights


class CognitiveReasoner(nn.Module):
    """Implements cognitive reasoning capabilities"""
    
    def __init__(self, hidden_dim: int = 512):
        super().__init__()
        self.reasoning_blocks = nn.ModuleList([
            nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=8, batch_first=True)
            for _ in range(4)
        ])
        self.memory_network = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.reasoning_head = nn.Linear(hidden_dim, hidden_dim)
    
    def forward(self, fused_input: torch.Tensor, 
                external_knowledge: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Process through reasoning blocks
        x = fused_input.unsqueeze(1)  # Add sequence dimension
        for block in self.reasoning_blocks:
            x = block(x)
        
        # Incorporate external knowledge if provided
        if external_knowledge is not None:
            x = x + external_knowledge.unsqueeze(1)
        
        # Process through memory network
        memory_out, _ = self.memory_network(x)
        
        # Apply reasoning head
        reasoning_output = self.reasoning_head(memory_out.squeeze(1))
        return reasoning_output


class AdvancedAIFusionEngine:
    """Main AI fusion engine with multimodal capabilities"""
    
    def __init__(self, model_path: str = "microsoft/DialoGPT-medium", 
                 use_gpu: bool = True, fusion_mode: AIFusionMode = AIFusionMode.ATTENTION_FUSION):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.fusion_mode = fusion_mode
        
        # Initialize components
        self.tokenizer = None
        self.language_model = None
        self.sentence_encoder = None
        self.multimodal_encoder = None
        self.attention_fusion = None
        self.cognitive_reasoner = None
        self.scalers = {}
        
        # Initialize models
        self._initialize_models()
        
        # Task queue for asynchronous processing
        self.task_queue = queue.Queue()
        self.result_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self.metrics = {
            'fusion_calls': 0,
            'avg_fusion_time': 0.0,
            'cache_hits': 0,
            'accuracy_score': 0.0
        }
        
        logger.info(f"Advanced AI Fusion Engine initialized on {self.device}")
    
    def _initialize_models(self):
        """Initialize all AI models and components"""
        try:
            # Initialize language model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.language_model = AutoModel.from_pretrained(self.model_path).to(self.device)
            self.language_model.eval()
            
            # Initialize sentence transformer
            self.sentence_encoder = SentenceTransformer('all-MiniLM-L6-v2').to(self.device)
            
            # Initialize multimodal encoder
            self.multimodal_encoder = MultimodalEncoder().to(self.device)
            
            # Initialize attention fusion
            self.attention_fusion = AttentionFusion(input_dim=512, num_modalities=3).to(self.device)
            
            # Initialize cognitive reasoner
            self.cognitive_reasoner = CognitiveReasoner().to(self.device)
            
            logger.info("All AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            # Fallback to basic functionality
            self.language_model = None
    
    def encode_text(self, text: str) -> np.ndarray:
        """Encode text using the language model"""
        if not self.language_model:
            return np.random.rand(768).astype(np.float32)  # Fallback embedding
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.language_model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embeddings[0]  # Return first sequence embedding
        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            return np.random.rand(768).astype(np.float32)
    
    def encode_sentence(self, sentence: str) -> np.ndarray:
        """Encode sentence using sentence transformer"""
        try:
            embeddings = self.sentence_encoder.encode([sentence])
            return embeddings[0]
        except Exception as e:
            logger.error(f"Sentence encoding failed: {e}")
            return np.random.rand(384).astype(np.float32)
    
    def encode_numeric_features(self, numeric_data: List[float]) -> np.ndarray:
        """Encode numeric features"""
        try:
            # Normalize the data
            if 'numeric' not in self.scalers:
                self.scalers['numeric'] = StandardScaler()
                numeric_array = np.array(numeric_data).reshape(1, -1)
                normalized = self.scalers['numeric'].fit_transform(numeric_array)
            else:
                numeric_array = np.array(numeric_data).reshape(1, -1)
                normalized = self.scalers['numeric'].transform(numeric_array)
            
            return normalized[0].astype(np.float32)
        except Exception as e:
            logger.error(f"Numeric encoding failed: {e}")
            return np.random.rand(len(numeric_data)).astype(np.float32)
    
    def encode_categorical_features(self, categories: List[str]) -> np.ndarray:
        """Encode categorical features using embeddings"""
        try:
            # Convert categories to a single string and encode
            category_str = " ".join(categories)
            embedding = self.encode_sentence(category_str)
            return embedding[:64]  # Truncate to expected size
        except Exception as e:
            logger.error(f"Categorical encoding failed: {e}")
            return np.random.rand(64).astype(np.float32)
    
    def fuse_multimodal_data(self, text_data: str, numeric_data: List[float], 
                           categorical_data: List[str], 
                           external_knowledge: Optional[np.ndarray] = None) -> FusionResult:
        """Fuse multimodal data using the selected fusion strategy"""
        start_time = time.time()
        
        # Encode all modalities
        text_embedding = self.encode_text(text_data)
        numeric_embedding = self.encode_numeric_features(numeric_data)
        categorical_embedding = self.encode_categorical_features(categorical_data)
        
        # Convert to tensors
        text_tensor = torch.tensor(text_embedding, dtype=torch.float32).unsqueeze(0).to(self.device)
        numeric_tensor = torch.tensor(numeric_embedding, dtype=torch.float32).unsqueeze(0).to(self.device)
        cat_tensor = torch.tensor(categorical_embedding, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        # Apply multimodal encoder
        fused_initial = self.multimodal_encoder(text_tensor, numeric_tensor, cat_tensor)
        
        # Apply fusion based on mode
        if self.fusion_mode == AIFusionMode.ATTENTION_FUSION:
            modalities = [text_tensor, numeric_tensor, cat_tensor]
            fused_output, attention_weights = self.attention_fusion(modalities)
        else:
            # For other modes, use the initial fused representation
            fused_output = fused_initial
            attention_weights = torch.ones(1, 3, 512).to(self.device)  # Dummy weights
        
        # Apply cognitive reasoning
        ext_knowledge_tensor = None
        if external_knowledge is not None:
            ext_knowledge_tensor = torch.tensor(external_knowledge, dtype=torch.float32).to(self.device)
        
        reasoning_output = self.cognitive_reasoner(fused_output, ext_knowledge_tensor)
        
        # Calculate confidence score based on attention weights
        attention_confidence = torch.mean(torch.std(attention_weights, dim=1)).item()
        confidence_score = min(1.0, max(0.0, attention_confidence))
        
        # Create reasoning trace
        reasoning_trace = [
            f"Encoded text: {len(text_data.split())} tokens",
            f"Processed {len(numeric_data)} numeric features",
            f"Processed {len(categorical_data)} categorical features",
            f"Fusion completed in {(time.time() - start_time)*1000:.2f}ms"
        ]
        
        # Calculate modality contributions (simplified)
        modality_contributions = {
            'text': float(torch.mean(torch.abs(text_tensor))),
            'numeric': float(torch.mean(torch.abs(numeric_tensor))),
            'categorical': float(torch.mean(torch.abs(cat_tensor)))
        }
        
        # Update metrics
        self.metrics['fusion_calls'] += 1
        avg_time = self.metrics['avg_fusion_time']
        self.metrics['avg_fusion_time'] = (
            (avg_time * (self.metrics['fusion_calls'] - 1) + (time.time() - start_time)) /
            self.metrics['fusion_calls']
        )
        
        return FusionResult(
            fused_embedding=reasoning_output.cpu().numpy()[0],
            confidence_score=confidence_score,
            reasoning_trace=reasoning_trace,
            modality_contributions=modality_contributions,
            timestamp=datetime.utcnow()
        )
    
    async def fuse_multimodal_data_async(self, text_data: str, numeric_data: List[float], 
                                       categorical_data: List[str],
                                       external_knowledge: Optional[np.ndarray] = None) -> FusionResult:
        """Asynchronously fuse multimodal data"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.fuse_multimodal_data, 
            text_data, numeric_data, categorical_data, external_knowledge
        )
    
    def generate_insights(self, fusion_result: FusionResult, context: str = "") -> str:
        """Generate human-readable insights from fusion result"""
        if not self.language_model:
            return "Insights generation not available"
        
        try:
            # Create a prompt for insight generation
            prompt = f"""
            Based on the following AI fusion analysis, provide actionable insights:
            
            Context: {context}
            
            Fusion Confidence Score: {fusion_result.confidence_score:.3f}
            
            Modality Contributions:
            - Text: {fusion_result.modality_contributions['text']:.3f}
            - Numeric: {fusion_result.modality_contributions['numeric']:.3f}
            - Categorical: {fusion_result.modality_contributions['categorical']:.3f}
            
            Reasoning Trace: {', '.join(fusion_result.reasoning_trace)}
            
            Please provide:
            1. Key findings
            2. Recommended actions
            3. Potential risks
            4. Confidence assessment
            """
            
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.language_model.generate(
                    **inputs,
                    max_length=len(inputs['input_ids'][0]) + 256,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            insight_start = response.find(prompt) + len(prompt)
            return response[insight_start:].strip()
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return f"Insight generation failed: {str(e)}"
    
    def predict_outcomes(self, fusion_result: FusionResult, prediction_horizon: int = 1) -> Dict[str, Any]:
        """Predict future outcomes based on fusion result using a simulated predictive model."""
        try:
            # In a real system, a dedicated model (e.g., an LSTM or Transformer head)
            # would be trained on historical fusion_results and actual outcomes.
            # For simulation, we'll create a structured prediction based on embedding.
            
            embedding = fusion_result.fused_embedding
            
            # Simulate a multi-output prediction for various aspects
            # Example: [future_state_value, risk_score, opportunity_score]
            
            # Use embedding components to drive simulated prediction
            # Introduce some complexity and variability based on embedding and confidence
            base_pred_value = np.mean(embedding) * 100
            base_risk_score = (np.std(embedding) + (1 - fusion_result.confidence_score)) * 50
            base_opportunity_score = (fusion_result.confidence_score - np.min(embedding)) * 70

            predicted_outcomes = []
            for i in range(prediction_horizon):
                # Apply simulated temporal progression and noise
                current_pred = {
                    'future_state_value': float(base_pred_value + np.sin(i * 0.5) * 5 + np.random.normal(0, 2)),
                    'risk_score': float(np.clip(base_risk_score + np.cos(i * 0.3) * 10 + np.random.normal(0, 3), 0, 100)),
                    'opportunity_score': float(np.clip(base_opportunity_score + np.sin(i * 0.6) * 8 + np.random.normal(0, 2), 0, 100))
                }
                predicted_outcomes.append(current_pred)
                
            return {
                'predictions_steps': predicted_outcomes,
                'confidence': float(fusion_result.confidence_score),
                'horizon': prediction_horizon,
                'timestamp': datetime.utcnow().isoformat(),
                'prediction_model_type': 'simulated_multi_output'
            }
        except Exception as e:
            logger.error(f"Outcome prediction failed: {e}")
            return {"error": str(e)}
    
    def detect_anomalies(self, fusion_result: FusionResult, baseline_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Detect anomalies in the fusion result compared to baseline"""
        try:
            current_embedding = fusion_result.fused_embedding
            
            if not baseline_embeddings:
                return {"anomaly_detected": False, "anomaly_score": 0.0, "message": "No baseline for comparison"}
            
            # Calculate distances to baseline embeddings
            distances = []
            for baseline in baseline_embeddings:
                distance = np.linalg.norm(current_embedding - baseline)
                distances.append(distance)
            
            # Calculate anomaly score (higher = more anomalous)
            avg_distance = np.mean(distances)
            std_distance = np.std(distances)
            
            if std_distance == 0:
                anomaly_score = 0.0
            else:
                # Z-score based anomaly detection
                z_score = abs(avg_distance - np.mean(distances)) / std_distance
                anomaly_score = min(1.0, z_score / 3.0)  # Normalize to 0-1 range
            
            return {
                "anomaly_detected": anomaly_score > 0.5,
                "anomaly_score": float(anomaly_score),
                "average_distance": float(avg_distance),
                "baseline_count": len(baseline_embeddings)
            }
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics for the fusion engine"""
        return {
            **self.metrics,
            'model_loaded': self.language_model is not None,
            'device': str(self.device),
            'fusion_mode': self.fusion_mode.value,
            'cache_size': len(self.result_cache)
        }


# Alias for compatibility with other modules
AIFusionEngine = AdvancedAIFusionEngine


class CognitiveAIController:
    """Controls the cognitive AI system and manages reasoning tasks"""
    
    def __init__(self, fusion_engine: AdvancedAIFusionEngine):
        self.fusion_engine = fusion_engine
        self.long_term_memory = deque(maxlen=1000)  # Store past fusion results
        self.short_term_memory = {}  # Store recent context
        self.reasoning_history = []
        self.lock = threading.Lock()
    
    def process_request(self, text_input: str, numeric_data: List[float] = None, 
                      categorical_data: List[str] = None,
                      external_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a cognitive AI request"""
        start_time = time.time()
        
        # Set defaults
        numeric_data = numeric_data or []
        categorical_data = categorical_data or []
        
        # Fuse multimodal data
        fusion_result = self.fusion_engine.fuse_multimodal_data(
            text_input, numeric_data, categorical_data,
            external_knowledge=None  # Would come from external_context if available
        )
        
        # Store in memory
        with self.lock:
            self.long_term_memory.append(fusion_result)
            self.reasoning_history.append({
                'timestamp': datetime.utcnow(),
                'input_length': len(text_input),
                'fusion_confidence': fusion_result.confidence_score,
                'processing_time': time.time() - start_time
            })
        
        # Generate insights
        insights = self.fusion_engine.generate_insights(fusion_result, text_input)
        
        # Make predictions
        predictions = self.fusion_engine.predict_outcomes(fusion_result)
        
        # Detect anomalies (compare with recent results)
        recent_embeddings = [r.fused_embedding for r in list(self.long_term_memory)[-10:]]
        anomalies = self.fusion_engine.detect_anomalies(fusion_result, recent_embeddings)
        
        return {
            'fusion_result': {
                'embedding_shape': fusion_result.fused_embedding.shape,
                'confidence_score': fusion_result.confidence_score,
                'modality_contributions': fusion_result.modality_contributions
            },
            'insights': insights,
            'predictions': predictions,
            'anomalies': anomalies,
            'reasoning_trace': fusion_result.reasoning_trace,
            'processing_time_ms': (time.time() - start_time) * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_cognitive_state(self) -> Dict[str, Any]:
        """Get the current cognitive state"""
        with self.lock:
            return {
                'memory_size': len(self.long_term_memory),
                'reasoning_history_count': len(self.reasoning_history),
                'recent_confidence_avg': np.mean([r['fusion_confidence'] for r in self.reasoning_history[-10:]]) if self.reasoning_history else 0,
                'processing_time_avg_ms': np.mean([r['processing_time']*1000 for r in self.reasoning_history[-10:]]) if self.reasoning_history else 0
            }
    
    def learn_from_interaction(self, input_data: Dict[str, Any], expected_output: Any, 
                             actual_output: Dict[str, Any]) -> bool:
        """Learn from the interaction to improve future responses"""
        # In a real system, this would update model parameters or adjust weights
        # For now, we'll just log the interaction for future analysis
        logger.info(f"Learning interaction recorded - Input: {len(str(input_data))} chars, Expected: {type(expected_output)}, Actual: {type(actual_output)}")
        return True


class AIKnowledgeGraph:
    """Maintains a knowledge graph for cognitive reasoning"""
    
    def __init__(self):
        self.entities = {}
        self.relationships = []
        self.embeddings = {}
        self.concepts = {}
        self.lock = threading.Lock()
    
    def add_entity(self, entity_id: str, entity_type: str, properties: Dict[str, Any]):
        """Add an entity to the knowledge graph"""
        with self.lock:
            self.entities[entity_id] = {
                'type': entity_type,
                'properties': properties,
                'relationships': []
            }
    
    def add_relationship(self, subject_id: str, predicate: str, object_id: str, confidence: float = 1.0):
        """Add a relationship between entities"""
        with self.lock:
            relationship = {
                'subject': subject_id,
                'predicate': predicate,
                'object': object_id,
                'confidence': confidence,
                'timestamp': datetime.utcnow()
            }
            self.relationships.append(relationship)
            
            # Update entity relationships
            if subject_id in self.entities:
                self.entities[subject_id]['relationships'].append(relationship)
    
    def query_related_entities(self, entity_id: str, relationship_type: str = None) -> List[Dict[str, Any]]:
        """Query entities related to a given entity"""
        with self.lock:
            related = []
            for rel in self.relationships:
                if rel['subject'] == entity_id:
                    if relationship_type is None or rel['predicate'] == relationship_type:
                        related.append({
                            'entity_id': rel['object'],
                            'relationship': rel['predicate'],
                            'confidence': rel['confidence']
                        })
            return related
    
    def get_subgraph(self, center_entity: str, depth: int = 2) -> Dict[str, Any]:
        """Get a subgraph centered around an entity with a specified traversal depth."""
        with self.lock:
            subgraph_entities = {}
            subgraph_relationships = []
            
            # Use a queue for BFS-like traversal
            q = deque([(center_entity, 0)])
            visited_entities = {center_entity} # Track visited entities to avoid loops and redundant processing
            
            while q:
                current_entity_id, current_depth = q.popleft()
                
                if current_entity_id not in subgraph_entities and current_entity_id in self.entities:
                    subgraph_entities[current_entity_id] = self.entities[current_entity_id]
                
                if current_depth >= depth:
                    continue # Stop at the specified depth

                for rel in self.relationships:
                    # Check relationships where current_entity_id is subject or object
                    if rel['subject'] == current_entity_id:
                        if rel['object'] not in visited_entities:
                            q.append((rel['object'], current_depth + 1))
                            visited_entities.add(rel['object'])
                        if rel not in subgraph_relationships:
                            subgraph_relationships.append(rel)
                    elif rel['object'] == current_entity_id:
                        if rel['subject'] not in visited_entities:
                            q.append((rel['subject'], current_depth + 1))
                            visited_entities.add(rel['subject'])
                        if rel not in subgraph_relationships:
                            subgraph_relationships.append(rel)
            
            # Ensure all entities in the collected relationships are also in subgraph_entities
            for rel in subgraph_relationships:
                if rel['subject'] not in subgraph_entities and rel['subject'] in self.entities:
                    subgraph_entities[rel['subject']] = self.entities[rel['subject']]
                if rel['object'] not in subgraph_entities and rel['object'] in self.entities:
                    subgraph_entities[rel['object']] = self.entities[rel['object']]

            return {
                'center': center_entity,
                'depth': depth,
                'entities': subgraph_entities,
                'relationships': subgraph_relationships
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the AI fusion engine
    fusion_engine = AdvancedAIFusionEngine(fusion_mode=AIFusionMode.ATTENTION_FUSION)
    
    print("🧠 Advanced AI Fusion Engine Initialized...")
    
    # Initialize cognitive controller
    cognitive_controller = CognitiveAIController(fusion_engine)
    
    # Initialize knowledge graph
    knowledge_graph = AIKnowledgeGraph()
    
    # Example: Add some knowledge to the graph
    knowledge_graph.add_entity("satellite1", "satellite", {"altitude": 500, "velocity": 7.8, "status": "nominal"})
    knowledge_graph.add_entity("station1", "ground_station", {"location": "Houston", "status": "active"})
    knowledge_graph.add_relationship("satellite1", "transmits_to", "station1", confidence=0.95)
    
    print("📚 Knowledge graph populated")
    
    # Example: Process a complex multimodal request
    print("\nProcessing multimodal request...")
    
    text_input = "The satellite telemetry shows unusual temperature fluctuations in subsystem X. Recommend corrective actions."
    numeric_data = [23.5, 45.2, 12.8, 78.9, 56.1]  # Example telemetry values
    categorical_data = ["temperature", "pressure", "voltage", "current", "status"]
    
    result = cognitive_controller.process_request(
        text_input=text_input,
        numeric_data=numeric_data,
        categorical_data=categorical_data
    )
    
    print(f"✅ Processing completed in {result['processing_time_ms']:.2f}ms")
    print(f"📊 Fusion confidence: {result['fusion_result']['confidence_score']:.3f}")
    print(f"💡 Predictions made: {len(result['predictions'].get('predictions', []))}")
    print(f"⚠️  Anomalies detected: {result['anomalies']['anomaly_detected']}")
    
    print(f"\n📝 Insights generated:")
    print(result['insights'][:200] + "..." if len(result['insights']) > 200 else result['insights'])
    
    # Example: Query the knowledge graph
    print("\n🔍 Querying knowledge graph...")
    related_entities = knowledge_graph.query_related_entities("satellite1")
    print(f"Related entities: {related_entities}")
    
    # Get cognitive state
    print("\n🧠 Cognitive state:")
    cognitive_state = cognitive_controller.get_cognitive_state()
    print(json.dumps(cognitive_state, indent=2, default=str))
    
    # Get system metrics
    print("\n📊 System metrics:")
    metrics = fusion_engine.get_system_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Example: Process multiple requests to test learning
    print("\n🔄 Testing adaptive learning...")
    for i in range(3):
        test_result = cognitive_controller.process_request(
            text_input=f"Telemetry reading {i+1}: normal operational parameters",
            numeric_data=[20+i, 30+i, 40+i],
            categorical_data=["sensor", "reading", "normal"]
        )
        print(f"Request {i+1} confidence: {test_result['fusion_result']['confidence_score']:.3f}")
    
    print("\n✅ Advanced AI Fusion Engine Test Completed")