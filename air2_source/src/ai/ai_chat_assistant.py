"""
AirOne Professional v4.0 - AI Chat Assistant
Advanced conversational AI with context awareness
"""
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class AIChatAssistant:
    """Advanced AI chat assistant with context awareness"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_window = 10
        self.persona = "AirOne Professional Assistant"
        self.capabilities = [
            "telemetry_analysis",
            "mission_planning",
            "system_diagnostics",
            "troubleshooting",
            "data_interpretation",
            "recommendations"
        ]
        
        # Load or create knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load AI knowledge base"""
        kb_file = self.model_dir / "knowledge_base.json"
        
        if kb_file.exists():
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default knowledge base
        return {
            'greetings': [
                "Hello! I'm your AirOne Professional Assistant.",
                "Hi there! How can I help you today?",
                "Welcome! Ready to assist with your mission."
            ],
            'telemetry_help': {
                'altitude': "Altitude data shows vertical position. Monitor for apogee detection.",
                'velocity': "Velocity indicates speed and direction. Negative values suggest descent.",
                'battery': "Battery level is critical for mission success. Plan recovery at 20%%.",
                'signal': "Signal strength affects data transmission. Optimal range: -40 to -70 dBm."
            },
            'troubleshooting': {
                'low_battery': "1. Reduce telemetry frequency 2. Enable power saving mode 3. Initiate recovery",
                'weak_signal': "1. Check antenna orientation 2. Increase transmitter power 3. Verify receiver location",
                'high_temp': "1. Check ventilation 2. Reduce CPU load 3. Monitor for thermal throttling"
            },
            'commands': {
                'status': "Get current system status",
                'telemetry': "View real-time telemetry data",
                'mission': "Get mission status and progress",
                'help': "Show available commands and features"
            }
        }
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process chat message and generate response
        
        Args:
            message: User message
            context: Optional context data (telemetry, mission state, etc.)
            
        Returns:
            Response dictionary
        """
        # Add to conversation history
        self.conversation_history.append({
            'role': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit history
        if len(self.conversation_history) > self.context_window * 2:
            self.conversation_history = self.conversation_history[-self.context_window * 2:]
        
        # Analyze message and generate response
        response = self._generate_response(message, context)
        
        # Add response to history
        self.conversation_history.append({
            'role': 'assistant',
            'message': response['response'],
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _generate_response(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI response"""
        message_lower = message.lower().strip()
        
        # Greeting detection
        if any(greet in message_lower for greet in ['hello', 'hi', 'hey', 'greetings']):
            import random
            return {
                'response': random.choice(self.knowledge_base['greetings']),
                'intent': 'greeting',
                'confidence': 0.95
            }
        
        # Telemetry queries
        if 'telemetry' in message_lower or 'altitude' in message_lower or 'velocity' in message_lower:
            if context and 'telemetry' in context:
                tel = context['telemetry']
                response = f"Current telemetry data:\n"
                response += f"  • Altitude: {tel.get('altitude', 0):.1f} m\n"
                response += f"  • Velocity: {tel.get('velocity', 0):.1f} m/s\n"
                response += f"  • Battery: {tel.get('battery', 0):.1f}%%\n"
                response += f"  • Signal: {tel.get('signal', 0)} dBm\n"
                
                if tel.get('altitude', 0) > 500:
                    response += "\n⚠️ High altitude detected - monitor for apogee"
                
                return {
                    'response': response,
                    'intent': 'telemetry_query',
                    'confidence': 0.90,
                    'data': tel
                }
            else:
                return {
                    'response': "No telemetry data available. Start a mission first.",
                    'intent': 'telemetry_query',
                    'confidence': 0.80
                }
        
        # Help requests
        if 'help' in message_lower or 'commands' in message_lower:
            response = "Available commands:\n"
            for cmd, desc in self.knowledge_base['commands'].items():
                response += f"  • {cmd} - {desc}\n"
            response += "\nYou can also ask about:\n"
            response += "  • Telemetry data (altitude, velocity, battery, signal)\n"
            response += "  • Mission status\n"
            response += "  • System diagnostics\n"
            response += "  • Troubleshooting"
            
            return {
                'response': response,
                'intent': 'help',
                'confidence': 0.95
            }
        
        # Status queries
        if 'status' in message_lower or 'state' in message_lower:
            if context and 'mission' in context:
                mission = context['mission']
                return {
                    'response': f"Mission Status: {mission.get('state', 'UNKNOWN')}\nProgress: {mission.get('progress', 0):.1f}%%",
                    'intent': 'status_query',
                    'confidence': 0.90
                }
            else:
                return {
                    'response': "System Status: ONLINE\nReady for operations",
                    'intent': 'status_query',
                    'confidence': 0.85
                }
        
        # Troubleshooting
        if 'problem' in message_lower or 'issue' in message_lower or 'error' in message_lower:
            response = "I can help troubleshoot. Please describe the specific issue:\n"
            response += "  • Battery problems\n"
            response += "  • Signal issues\n"
            response += "  • Temperature concerns\n"
            response += "  • Other problems"
            
            return {
                'response': response,
                'intent': 'troubleshooting',
                'confidence': 0.75
            }
        
        # Default response
        return {
            'response': "I'm here to help with your AirOne mission. You can ask me about:\n  • Telemetry data\n  • Mission status\n  • System health\n  • Troubleshooting\n\nType 'help' for available commands.",
            'intent': 'general',
            'confidence': 0.60
        }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        user_messages = [m for m in self.conversation_history if m['role'] == 'user']
        assistant_messages = [m for m in self.conversation_history if m['role'] == 'assistant']
        
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'started_at': self.conversation_history[0]['timestamp'] if self.conversation_history else None,
            'last_message': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def export_conversation(self, filename: Optional[str] = None) -> str:
        """Export conversation to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        filepath = self.model_dir / filename
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'persona': self.persona,
            'conversation': self.conversation_history,
            'summary': self.get_conversation_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return str(filepath)


class AIRecommendationEngine:
    """AI-powered recommendation engine"""
    
    def __init__(self):
        self.rules = self._load_recommendation_rules()
    
    def _load_recommendation_rules(self) -> List[Dict[str, Any]]:
        """Load recommendation rules"""
        return [
            {
                'condition': lambda tel: tel.get('battery', 100) < 20,
                'recommendation': "CRITICAL: Battery below 20%% - initiate immediate recovery",
                'priority': 'critical'
            },
            {
                'condition': lambda tel: tel.get('battery', 100) < 40,
                'recommendation': "WARNING: Battery below 40%% - consider ending mission",
                'priority': 'warning'
            },
            {
                'condition': lambda tel: tel.get('signal', 0) < -80,
                'recommendation': "WARNING: Weak signal - check antenna and receiver position",
                'priority': 'warning'
            },
            {
                'condition': lambda tel: tel.get('altitude', 0) > 800,
                'recommendation': "INFO: High altitude achieved - monitor for apogee",
                'priority': 'info'
            },
            {
                'condition': lambda tel: tel.get('velocity', 0) < -30,
                'recommendation': "INFO: Rapid descent detected - prepare for landing",
                'priority': 'info'
            },
            {
                'condition': lambda tel: tel.get('temperature', 25) > 45,
                'recommendation': "WARNING: High temperature - monitor system health",
                'priority': 'warning'
            }
        ]
    
    def get_recommendations(self, telemetry: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get recommendations based on telemetry"""
        recommendations = []
        
        for rule in self.rules:
            try:
                if rule['condition'](telemetry):
                    recommendations.append({
                        'recommendation': rule['recommendation'],
                        'priority': rule['priority']
                    })
            except Exception as e:
                logger.error(f"Recommendation rule error: {e}")
        
        # Sort by priority
        priority_order = {'critical': 0, 'warning': 1, 'info': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations


# Global instances
_chat_assistant: Optional[AIChatAssistant] = None
_recommendation_engine: Optional[AIRecommendationEngine] = None


def get_chat_assistant() -> AIChatAssistant:
    """Get chat assistant instance"""
    global _chat_assistant
    if _chat_assistant is None:
        _chat_assistant = AIChatAssistant()
    return _chat_assistant


def get_recommendations(telemetry: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get AI recommendations"""
    engine = AIRecommendationEngine()
    return engine.get_recommendations(telemetry)


def chat(message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Quick chat function"""
    return get_chat_assistant().chat(message, context)


if __name__ == "__main__":
    # Test AI chat
    print("="*70)
    print("  AirOne Professional v4.0 - AI Chat Assistant Test")
    print("="*70)
    print()
    
    assistant = AIChatAssistant()
    
    # Test conversations
    test_messages = [
        "Hello",
        "What's the status?",
        "Show me telemetry",
        "Help me troubleshoot",
        "What commands are available?"
    ]
    
    context = {
        'telemetry': {
            'altitude': 523.5,
            'velocity': 25.3,
            'battery': 35.2,
            'signal': -65
        },
        'mission': {
            'state': 'ASCENT',
            'progress': 65.0
        }
    }
    
    for message in test_messages:
        print(f"User: {message}")
        response = assistant.chat(message, context)
        print(f"AI: {response['response']}")
        print(f"Intent: {response['intent']} (confidence: {response['confidence']:.2f})")
        print()
    
    # Test recommendations
    print("Testing AI Recommendations:")
    print("-"*40)
    engine = AIRecommendationEngine()
    recs = engine.get_recommendations(context['telemetry'])
    
    for rec in recs:
        print(f"[{rec['priority'].upper()}] {rec['recommendation']}")
    
    print()
    print("="*70)
    print("  AI Chat Assistant Test Complete")
    print("="*70)
