"""
AirOne v3 - Scientific Analysis Core & Models
=============================================

This file contains the primary scientific analysis orchestration engine
and high-level analysis tools, along with the underlying physics, 
mathematical, and statistical models used by the analysis engine.

This file consolidates:
- src/analysis/core.py (The primary analysis orchestration engine)
- src/analysis/models.py (Physics, mathematical, and statistical models)
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger("AnalysisCore")

class AtmosphereModel:
    """
    Advanced Atmospheric Physics Model
    - Barometric Formula with Lapse Rate
    - Hypsometric Equation
    - Density Altitude
    - Dew Point (Magnus Formula)
    """
    R_AIR = 287.05
    G = 9.80665
    P0 = 101325.0

    @staticmethod
    def calculate_density_altitude(pressure_pa, temp_c):
        pressure_alt_m = 44330 * (1 - (pressure_pa / AtmosphereModel.P0)**(1/5.255))
        isa_temp_c = 15.0 - (0.0065 * pressure_alt_m)
        return pressure_alt_m + 120 * 0.3048 * (temp_c - isa_temp_c)

    @staticmethod
    def calculate_dew_point(temp_c, rh_percent):
        if rh_percent <= 0: return -273.15
        b, c = 17.62, 243.12
        gamma = (b * temp_c / (c + temp_c)) + np.log(rh_percent / 100.0)
        return (c * gamma) / (b - gamma)

class GasDispersionEngine:
    """
    Gaussian Plume Model for Gas Dispersion.
    """
    @staticmethod
    def gaussian_plume_concentration(x, y, z, H, Q, u, stability_class="D"):
        if x <= 0 or u < 0.1: return 0.0

        params = {"A": (0.22, 0.20), "B": (0.16, 0.12), "C": (0.11, 0.08), "D": (0.08, 0.06)}
        sy_coeff, sz_coeff = params.get(stability_class, params["D"])

        sigma_y = sy_coeff * x * (1 + 0.0001*x)**(-0.5)
        sigma_z = sz_coeff * x

        term1 = Q / (2 * np.pi * u * sigma_y * sigma_z)
        term2 = np.exp( - (y**2) / (2 * sigma_y**2) )
        term3 = np.exp( - ((z - H)**2) / (2 * sigma_z**2) ) + np.exp( - ((z + H)**2) / (2 * sigma_z**2) )

        return term1 * term2 * term3

class RadiationModel:
    """
    Radiation and Space Weather Physics
    """
    @staticmethod
    def cosmic_ray_flux_estimate(altitude_m, latitude_deg):
        alt_factor = np.exp(altitude_m / 4000.0)
        if altitude_m > 20000:
             alt_factor = np.exp(5.0) * (0.9 ** ((altitude_m - 20000)/5000))
        lat_factor = 1.0 + (abs(latitude_deg) / 90.0)
        return 2.0 * alt_factor * lat_factor

    @staticmethod
    def detect_burst(window_data, current_val, threshold_sigma=3.0):
        if len(window_data) < 10: return False, 0.0
        mu, sigma = np.mean(window_data), np.std(window_data)
        if sigma == 0: return False, 0.0
        z = (current_val - mu) / sigma
        return (z > threshold_sigma), z

class AdvancedStatistics:
    """
    Advanced Statistical Methods for Scientific Analysis.
    """
    @staticmethod
    def weighted_least_squares(x: np.ndarray, y: np.ndarray, weights: np.ndarray) -> Tuple[float, float, float]:
        if len(x) != len(y) or len(x) < 2: return 0.0, 0.0, 0.0

        w = weights / np.sum(weights)
        x_mean, y_mean = np.sum(x * w), np.sum(y * w)

        num = np.sum(w * (x - x_mean) * (y - y_mean))
        den = np.sum(w * (x - x_mean)**2)

        if den == 0: return 0.0, 0.0, 0.0

        slope = num / den
        intercept = y_mean - slope * x_mean

        y_pred = slope * x + intercept
        ss_res = np.sum(weights * (y - y_pred)**2)
        ss_tot = np.sum(weights * (y - y_mean)**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return slope, intercept, r2

    @staticmethod
    def gmm_1d_clustering(data: np.ndarray, n_components: int = 2, max_iter: int = 100) -> Dict[str, Any]:
        n = len(data)
        if n < n_components: return {}

        means = np.linspace(np.min(data), np.max(data), n_components)
        variances = np.ones(n_components) * np.var(data)
        weights = np.ones(n_components) / n_components

        for _ in range(max_iter):
            probs = np.zeros((n, n_components))
            for k in range(n_components):
                p = (1/np.sqrt(2*np.pi*variances[k]))*np.exp(-0.5*((data-means[k])**2/variances[k]))
                probs[:, k] = weights[k] * p

            row_sums = probs.sum(axis=1)
            probs[row_sums > 0] = probs[row_sums > 0] / row_sums[row_sums > 0, np.newaxis]

            Nk = probs.sum(axis=0)
            new_means = np.sum(probs * data[:, np.newaxis], axis=0) / (Nk + 1e-6)

            if np.allclose(means, new_means, atol=1e-4): break
            means = new_means

        return {'means': means.tolist(), 'variances': variances.tolist(), 'weights': weights.tolist()}

    @staticmethod
    def modified_z_score(data: np.ndarray) -> np.ndarray:
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad == 0: return np.zeros_like(data)
        return 0.6745 * (data - median) / mad

class VerticalProfiler:
    """
    Groups telemetry data into altitude bins to create vertical profiles.
    Useful for detecting atmospheric layers, inversions, and lapse rates.
    """
    def __init__(self, bin_size_m: float = 100.0):
        self.bin_size = bin_size_m
        self.bins = defaultdict(list)

    def add_data(self, altitude: float, data_point: Dict[str, float]):
        """
        Add a data point to the appropriate bin.
        data_point should be a dict of metrics (e.g. {'temp': 20, 'humidity': 50})
        """
        bin_idx = int(altitude // self.bin_size)
        self.bins[bin_idx].append(data_point)

    def get_profile(self) -> Dict[str, Dict[str, float]]:
        """
        Returns aggregated stats per bin.
        Format: { bin_start_alt: { 'temp_mean': 15.0, ... } }
        """
        profile = {}
        for bin_idx, data_list in sorted(self.bins.items()):
            alt_start = bin_idx * self.bin_size
            stats = {}

            keys = data_list[0].keys() if data_list else []
            for k in keys:
                values = [d[k] for d in data_list if k in d]
                if values:
                    stats[f"{k}_mean"] = np.mean(values)
                    stats[f"{k}_std"] = np.std(values)

            stats['count'] = len(data_list)
            profile[alt_start] = stats

        return profile

class GeospatialMapper:
    """
    Accumulates data into geospatial tiles for mapping.
    """
    def __init__(self, tile_size_deg: float = 0.001): # approx 100m
        self.tile_size = tile_size_deg
        self.tiles = defaultdict(list)

    def add_point(self, lat: float, lon: float, value: float):
        lat_idx = int(lat // self.tile_size)
        lon_idx = int(lon // self.tile_size)
        self.tiles[(lat_idx, lon_idx)].append(value)

    def get_grid(self) -> Dict[Tuple[float, float], float]:
        """Returns {(lat_center, lon_center): mean_value}"""
        grid = {}
        for (lat_idx, lon_idx), values in self.tiles.items():
            lat_center = (lat_idx + 0.5) * self.tile_size
            lon_center = (lon_idx + 0.5) * self.tile_size
            grid[(lat_center, lon_center)] = np.mean(values)
        return grid

class TelemetryAudit:
    """
    Analyzes telemetry stream for link quality and time sync issues.
    """
    def __init__(self):
        self.last_packet_id = -1
        self.packet_loss_count = 0
        self.total_packets = 0
        self.latencies = []

    def process_packet(self, packet_id: int, timestamp: float, server_time: float):
        if self.last_packet_id != -1 and packet_id > self.last_packet_id + 1:
            self.packet_loss_count += (packet_id - self.last_packet_id - 1)

        self.latencies.append(server_time - timestamp)
        self.last_packet_id = packet_id
        self.total_packets += 1

    def get_stats(self) -> Dict[str, float]:
        if self.total_packets == 0: return {}

        return {
            "total_packets": self.total_packets,
            "loss_rate": self.packet_loss_count / (self.total_packets + self.packet_loss_count),
            "latency_jitter": np.std(self.latencies) if self.latencies else 0
        }

class CorrelationEngine:
    """
    Finds correlations between time-series data windows.
    """
    def correlate(self, series_a: List[float], series_b: List[float]) -> float:
        if len(series_a) != len(series_b) or len(series_a) < 10:
            return 0.0
        return float(np.corrcoef(series_a, series_b)[0, 1])

class EventSummarizer:
    """
    Generates concise natural language summaries for flagged events.
    """
    def summarize_event(self, event_type: str, metrics: Dict[str, float], timestamp: float) -> str:
        summary = f"Event at T+{timestamp:.1f}s: {event_type}. "
        if event_type == "RadiationBurst":
            summary += f"Spike to {metrics.get('radiation', 0):.2f} uSv/h at {metrics.get('altitude', 0):.0f}m."
        else:
            top_factors = sorted(metrics.items(), key=lambda x: abs(x[1]), reverse=True)[:2]
            summary += f"Factors: {', '.join([f'{k}={v:.1f}' for k, v in top_factors])}."
        return summary

class ScientificAnalysisCore:
    """
    Core scientific analysis engine for AirOne. This is the main entry point
    for performing analysis on telemetry records.
    """

    def __init__(self):
        self.history = []
        self.max_history = 1000
        self.layers: Dict[int, List[float]] = {}

    def analyze(self, record: Any) -> Dict[str, Any]:
        """Performs comprehensive analysis on a TelemetryRecord"""
        self._update_history(record)
        metrics = {}
        metrics.update(self._analyze_atmosphere(record))
        metrics.update(self._analyze_radiation(record))
        metrics.update(self._analyze_dynamics(record))
        # Add more analysis domains here
        return metrics

    def _update_history(self, rec):
        self.history.append(rec)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def _analyze_atmosphere(self, rec):
        da = AtmosphereModel.calculate_density_altitude(rec.pressure, rec.temperature)
        dew_point = AtmosphereModel.calculate_dew_point(rec.temperature, rec.humidity)

        # Inversion Detection Logic
        has_inversion = False
        if len(self.history) > 10:
             prev = self.history[-10]
             dT = rec.temperature - prev.temperature
             dAlt = rec.altitude_baro - prev.altitude_baro
             if dAlt > 5 and dT > 0.5:
                 has_inversion = True

        return {
            'density_altitude': da,
            'dew_point': dew_point,
            'inversion_detected': has_inversion
        }

    def _analyze_radiation(self, rec):
        flux_baseline = RadiationModel.cosmic_ray_flux_estimate(rec.altitude_gnss, rec.latitude)

        is_burst = False
        if len(self.history) > 20:
             recent_doses = [r.radiation_dose for r in self.history[-20:]]
             is_burst, z_score = RadiationModel.detect_burst(recent_doses, rec.radiation_dose)

        return {
            'rad_burst_detected': is_burst,
            'cosmic_flux_baseline': flux_baseline
        }

    def _analyze_dynamics(self, rec):
        # Simplified drag coeff estimation
        est_cd = 0.0
        if rec.vertical_velocity < -1.0:
            rho = (rec.pressure * 100.0) / (287.05 * (rec.temperature + 273.15))
            if rho > 0:
                est_cd = (2 * 1.0 * 9.81) / (rho * (rec.vertical_velocity**2) * 0.1)

        return {
            'descent_cd_estimate': est_cd
        }

# Main execution block for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Launching AirOne v3 Scientific Analysis Core Test Suite 🚀")

    # --- Test Scientific Analysis Core ---
    print("\n--- Testing Scientific Analysis Core ---")
    analysis_core = ScientificAnalysisCore()
    
    # Create a mock telemetry record for testing
    class MockRecord:
        def __init__(self):
            self.pressure = 101325.0
            self.temperature = 20.0
            self.humidity = 50.0
            self.altitude_gnss = 100.0
            self.latitude = 34.0
            self.radiation_dose = 2.0
            self.altitude_baro = 100.0
            self.vertical_velocity = -5.0
    
    mock_record = MockRecord()
    analysis_results = analysis_core.analyze(mock_record)
    print("Analysis Results:")
    for key, value in analysis_results.items():
        print(f"  {key}: {value}")

    # --- Test Vertical Profiler ---
    print("\n--- Testing Vertical Profiler ---")
    profiler = VerticalProfiler(bin_size_m=50.0)
    for i in range(10):
        altitude = i * 25.0
        data = {'temp': 20 - i*0.5, 'humidity': 50 + i*2}
        profiler.add_data(altitude, data)
    
    profile = profiler.get_profile()
    print("Vertical Profile:")
    for alt, stats in profile.items():
        print(f"  Altitude {alt}m: {stats}")

    # --- Test Geospatial Mapper ---
    print("\n--- Testing Geospatial Mapper ---")
    mapper = GeospatialMapper(tile_size_deg=0.001)
    for i in range(10):
        lat = 34.0 + i * 0.0001
        lon = -118.0 + i * 0.0001
        value = 100 + i * 5
        mapper.add_point(lat, lon, value)
    
    grid = mapper.get_grid()
    print(f"Geospatial grid created with {len(grid)} tiles")

    # --- Test Telemetry Audit ---
    print("\n--- Testing Telemetry Audit ---")
    audit = TelemetryAudit()
    for i in range(10):
        audit.process_packet(i, i*10, i*10 + 0.1)
    
    stats = audit.get_stats()
    print("Telemetry Audit Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # --- Test Correlation Engine ---
    print("\n--- Testing Correlation Engine ---")
    corr_engine = CorrelationEngine()
    series_a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    series_b = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfect correlation
    correlation = corr_engine.correlate(series_a, series_b)
    print(f"Correlation between series: {correlation:.3f}")

    # --- Test Advanced Statistics ---
    print("\n--- Testing Advanced Statistics ---")
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])
    weights = np.array([1, 1, 1, 1, 1])
    slope, intercept, r2 = AdvancedStatistics.weighted_least_squares(x, y, weights)
    print(f"WLS Result: slope={slope:.3f}, intercept={intercept:.3f}, r2={r2:.3f}")

    data = np.array([1, 2, 3, 4, 5, 100])  # Contains outlier
    z_scores = AdvancedStatistics.modified_z_score(data)
    print(f"Modified Z-scores: {z_scores}")

    print("\n✅ Scientific Analysis Core & Models test suite finished.")