"""
Weather Module
Weather data and forecasting
"""

import numpy as np
from typing import Dict


class WeatherData:
    """Weather data"""
    
    def __init__(self):
        self.temperature = 20.0
        self.humidity = 50.0
        self.pressure = 1013.25
        self.wind_speed = 0.0
        self.wind_direction = 0.0
    
    def get_current(self) -> Dict:
        """Get current weather"""
        return {
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction
        }
    
    def update(self, data: Dict):
        """Update weather data"""
        self.temperature = data.get('temperature', self.temperature)
        self.humidity = data.get('humidity', self.humidity)
        self.pressure = data.get('pressure', self.pressure)
        self.wind_speed = data.get('wind_speed', self.wind_speed)
        self.wind_direction = data.get('wind_direction', self.wind_direction)


class WeatherForecast:
    """Weather forecast"""
    
    def __init__(self):
        pass
    
    def forecast(self, days: int = 7) -> list:
        """Generate forecast"""
        forecast = []
        for i in range(days):
            forecast.append({
                'day': i + 1,
                'temp_high': 20 + np.random.randint(-5, 5),
                'temp_low': 10 + np.random.randint(-5, 5),
                'condition': np.random.choice(['sunny', 'cloudy', 'rainy'])
            })
        return forecast


# Example
if __name__ == "__main__":
    w = WeatherData()
    print(w.get_current())