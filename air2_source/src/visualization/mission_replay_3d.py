"""
Mission Replay 3D Visualization for AirOne Professional v4.0
Generates interactive 3D WebGL plots of the flight trajectory using Plotly.
"""
import logging
import json
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MissionReplay3D:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MissionReplay3D")
        self.trajectory_data = []
        self.is_recording = False
        self.logger.info("Mission Replay 3D Engine Initialized.")

    def start_recording(self):
        self.is_recording = True
        self.trajectory_data = []
        self.logger.info("Started recording 3D trajectory data.")

    def add_point(self, x: float, y: float, z: float, timestamp: float = 0.0):
        if self.is_recording:
            self.trajectory_data.append({"x": x, "y": y, "z": z, "t": timestamp})

    def stop_recording(self):
        self.is_recording = False
        self.logger.info(f"Stopped recording. Total points: {len(self.trajectory_data)}")

    def generate_html_report(self, filepath: str = "logs/mission_replay.html") -> bool:
        """Generates a standalone HTML file with a Plotly 3D scatter plot."""
        if not self.trajectory_data:
            self.logger.warning("No trajectory data to export.")
            return False

        try:
            import plotly.graph_objects as go
            
            x_vals = [pt['x'] for pt in self.trajectory_data]
            y_vals = [pt['y'] for pt in self.trajectory_data]
            z_vals = [pt['z'] for pt in self.trajectory_data]

            fig = go.Figure(data=[go.Scatter3d(
                x=x_vals,
                y=y_vals,
                z=z_vals,
                mode='lines+markers',
                marker=dict(
                    size=4,
                    color=z_vals,                # set color to an array/list of desired values
                    colorscale='Viridis',        # choose a colorscale
                    opacity=0.8
                ),
                line=dict(
                    color='darkblue',
                    width=2
                )
            )])

            fig.update_layout(
                title="AirOne Mission 3D Trajectory Replay",
                margin=dict(l=0, r=0, b=0, t=40),
                scene=dict(
                    xaxis_title='Longitude Offset (m)',
                    yaxis_title='Latitude Offset (m)',
                    zaxis_title='Altitude (m)'
                )
            )

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            fig.write_html(filepath)
            self.logger.info(f"Successfully generated 3D replay at {filepath}")
            return True
            
        except ImportError:
            self.logger.warning("Plotly is not installed. Saving raw JSON trajectory instead.")
            with open(filepath.replace('.html', '.json'), 'w') as f:
                json.dump(self.trajectory_data, f)
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate 3D replay: {e}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    replay = MissionReplay3D()
    replay.start_recording()
    replay.add_point(0, 0, 0)
    replay.add_point(10, 10, 100)
    replay.add_point(20, 20, 150)
    replay.stop_recording()
    replay.generate_html_report("logs/test_replay.html")
