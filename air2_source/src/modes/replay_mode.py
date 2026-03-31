"""
Replay Mode for AirOne v3.0
Implements the replay operational mode
"""

import logging
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np # For potential data simulation

# Assuming some form of data sink for replayed data (e.g., a queue, or a direct call)
# For now, we will just log the replayed data.


class ReplayMode:
    """Replay operational mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.name = "Replay/Forensic Mode"
        self.description = "Historical data analysis and deterministic replay"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = config or {
            'data_file': 'simulated_telemetry.json',  # Default data file
            'playback_speed': 1.0, # 1.0 means real-time, >1 faster, <1 slower
            'loop_replay': False # Whether to loop the replay
        }
        self.replay_data = []
        self.replay_thread = None
        self.current_replay_index = 0

    def start(self):
        """Start the replay mode"""
        self.logger.info(f"Starting {self.name}...")
        self.logger.info(self.description)
        
        if not self._load_replay_data():
            self.logger.error(f"Failed to load replay data from {self.config['data_file']}. Cannot start Replay Mode.")
            return False

        self.running = True
        self.replay_thread = threading.Thread(target=self._replay_data_loop, daemon=True)
        self.replay_thread.start()
        
        self.logger.info(f"Replay Mode started. Replaying {len(self.replay_data)} packets at {self.config['playback_speed']}x speed.")
        return True

    def stop(self):
        """Stop the replay mode"""
        self.logger.info("Stopping Replay Mode...")
        self.running = False
        
        if self.replay_thread and self.replay_thread.is_alive():
            self.logger.info("Joining replay data thread...")
            self.replay_thread.join(timeout=5)
            if self.replay_thread.is_alive():
                self.logger.warning("Replay data thread did not terminate in time.")
            else:
                self.logger.info("Replay data thread terminated.")
        
        self.logger.info("Replay Mode stopped.")

    def _load_replay_data(self) -> bool:
        """Loads historical telemetry data from the configured file."""
        data_file = self.config['data_file']
        try:
            with open(data_file, 'r') as f:
                self.replay_data = json.load(f)
            self.logger.info(f"Successfully loaded {len(self.replay_data)} data packets from {data_file}.")
            # Ensure data is sorted by timestamp for deterministic replay
            self.replay_data.sort(key=lambda p: p.get('timestamp', '0'))
            return True
        except FileNotFoundError:
            self.logger.error(f"Replay data file not found: {data_file}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from {data_file}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while loading replay data: {e}")
            return False

    def _replay_data_loop(self):
        """Main loop for replaying historical data."""
        self.current_replay_index = 0
        while self.running:
            if self.current_replay_index >= len(self.replay_data):
                if self.config['loop_replay']:
                    self.logger.info("Replay finished, looping back to start.")
                    self.current_replay_index = 0
                else:
                    self.logger.info("Replay finished. Stopping replay thread.")
                    self.running = False
                    break

            packet = self.replay_data[self.current_replay_index]
            self.logger.debug(f"Replaying packet {self.current_replay_index}: {packet.get('altitude')}m, {packet.get('temperature')}C")
            
            # Simulate processing/feeding the packet to other system components
            self._feed_replayed_data(packet)

            self.current_replay_index += 1
            
            # Calculate sleep time based on playback speed (assuming packets have timestamp differences)
            if self.current_replay_index < len(self.replay_data):
                current_time_str = packet.get('timestamp')
                next_time_str = self.replay_data[self.current_replay_index].get('timestamp')
                
                if current_time_str and next_time_str:
                    try:
                        current_time = datetime.fromisoformat(current_time_str.replace('Z', '+00:00'))
                        next_time = datetime.fromisoformat(next_time_str.replace('Z', '+00:00'))
                        time_diff = (next_time - current_time).total_seconds()
                        sleep_duration = time_diff / self.config['playback_speed']
                        if sleep_duration > 0:
                            time.sleep(sleep_duration)
                    except ValueError:
                        self.logger.warning("Timestamp format error, using default sleep duration.")
                        time.sleep(1.0 / self.config['playback_speed'])
                else:
                    time.sleep(1.0 / self.config['playback_speed'])
            else: # If it's the last packet
                 time.sleep(1.0 / self.config['playback_speed']) # Short delay before checking loop_replay or exiting

        self.logger.info("Replay data loop terminated.")

    def _feed_replayed_data(self, packet: Dict[str, Any]):
        """Simulates feeding replayed data to other system components."""
        # In a real system, this would push data to a telemetry processor, GUI, etc.
        # For now, we just log it.
        self.logger.debug(f"Fed replayed data: Packet ID {packet.get('packet_id', 'N/A')}")
        # Example: telemetry_processor.process(packet)

    def get_replay_status(self) -> Dict[str, Any]:
        """Returns the current status of the replay mode."""
        return {
            "mode_name": self.name,
            "description": self.description,
            "running": self.running,
            "data_file": self.config['data_file'],
            "playback_speed": self.config['playback_speed'],
            "loop_replay": self.config['loop_replay'],
            "total_packets": len(self.replay_data),
            "current_packet_index": self.current_replay_index,
            "packets_remaining": max(0, len(self.replay_data) - self.current_replay_index),
            "last_replayed_packet": self.replay_data[self.current_replay_index - 1] if self.current_replay_index > 0 else {}
        }