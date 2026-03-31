"""
AirOne Report Generator
AI report generation functionality
"""

from typing import Dict, Any, List
from datetime import datetime


class ReportGenerator:
    """Generate AI analysis reports"""
    
    def __init__(self):
        self.reports = []
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report from analysis results"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_results': analysis_results,
            'summary': self._generate_summary(analysis_results),
            'recommendations': self._generate_recommendations(analysis_results)
        }
        self.reports.append(report)
        return report
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a more informative summary from analysis results."""
        summary_parts = [f"Analysis completed at {datetime.utcnow().isoformat()}."]

        # General status
        summary_parts.append("Overall System Status: Operational.")

        # Predictions summary
        predictions_info = results.get('predictions', {})
        predicted_values = predictions_info.get('values', [])
        if predicted_values:
            avg_pred = np.mean(predicted_values) if predicted_values else 0
            summary_parts.append(f"Predicted average metric: {avg_pred:.2f} over {len(predicted_values)} steps.")
        
        # Anomaly summary
        anomalies_info = results.get('anomalies', {})
        anomaly_count = anomalies_info.get('count', 0)
        if anomaly_count > 0:
            summary_parts.append(f"Detected {anomaly_count} anomalies. Review anomaly details for severity.")
        else:
            summary_parts.append("No significant anomalies detected.")
            
        # Mission phase summary
        phase_info = results.get('phase_classifications', {})
        if phase_info.get('details'):
            current_phase = phase_info['details'][-1].get('phase_name', 'unknown')
            summary_parts.append(f"Current Mission Phase: {current_phase}.")

        # Framework usage
        framework_summary = results.get('framework_summary', "AI frameworks utilized: N/A")
        if isinstance(framework_summary, dict) and framework_summary.get('available_frameworks'):
             summary_parts.append(f"AI Frameworks: {framework_summary['available_frameworks']} are active.")
        elif isinstance(framework_summary, str):
            summary_parts.append(framework_summary)


        return " ".join(summary_parts)
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from analysis results."""
        recommendations = []

        # Recommendations based on anomalies
        anomalies_info = results.get('anomalies', {})
        anomaly_count = anomalies_info.get('count', 0)
        if anomaly_count > 0:
            recommendations.append(f"Investigate {anomaly_count} detected anomalies immediately. Prioritize high-severity alerts.")
            for anomaly in anomalies_info.get('details', []):
                if anomaly.get('severity') in ['high', 'critical']:
                    recommendations.append(f"CRITICAL: Review data point at index {anomaly.get('index')} due to {anomaly.get('source')} anomaly.")
        else:
            recommendations.append("No significant anomalies observed. Continue routine monitoring.")

        # Recommendations based on predictions and confidence
        predictions_info = results.get('predictions', {})
        predicted_values = predictions_info.get('values', [])
        confidence_scores = predictions_info.get('confidences', [])
        
        if predicted_values and confidence_scores:
            min_confidence = min(confidence_scores)
            avg_confidence = np.mean(confidence_scores)
            if min_confidence < 0.6:
                recommendations.append(f"Some predictions have low confidence ({min_confidence:.2f}). Consider gathering more data or re-evaluating model reliability.")
            elif avg_confidence < 0.8:
                recommendations.append(f"Average prediction confidence is moderate ({avg_confidence:.2f}). Enhanced sensor data might improve accuracy.")

        # Recommendations based on mission phase
        phase_info = results.get('phase_classifications', {})
        if phase_info.get('details'):
            current_phase = phase_info['details'][-1].get('phase_name', 'unknown')
            if "Ascent" in current_phase:
                recommendations.append(f"Currently in {current_phase} phase. Monitor ascent rate and fuel consumption.")
            elif "Descent" in current_phase:
                recommendations.append(f"Currently in {current_phase} phase. Prepare for landing sequence and check parachute deployment parameters.")
            elif "Recovery" in current_phase:
                recommendations.append(f"Currently in {current_phase} phase. Initiate recovery protocols and locate payload.")
        
        if not recommendations:
            recommendations.append("All systems appear normal; no specific recommendations at this time.")

        return recommendations
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reports"""
        return self.reports[-limit:]


__all__ = ['ReportGenerator']
