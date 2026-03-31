"""
EMP Resilience Analyzer (ERA) for AirOne Professional v4.0
Models shielding effectiveness and component vulnerability to electromagnetic pulses.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EMPAnalyzer:
    def __init__(self, shielding_thickness_mm: float = 2.0, shielding_material: str = "Aluminium"):
        self.logger = logging.getLogger(f"{__name__}.ERA")
        self.thickness = shielding_thickness_mm
        self.material = shielding_material
        # Material conductivity relative to copper
        self.conductivity = {"Aluminium": 0.61, "Copper": 1.0, "Steel": 0.1}[material]
        self.logger.info(f"EMP Resilience Analyzer Initialized ({material} {thickness}mm).")

    def analyze_pulse(self, field_strength_kv_m: float, frequency_mhz: float) -> Dict[str, Any]:
        """Calculates attenuation and predicts component survivability."""
        # 1. Calculation of Skin Depth (m)
        # delta = 1 / sqrt(pi * f * mu * sigma)
        mu0 = 4 * math.pi * 1e-7
        sigma = self.conductivity * 5.8e7
        freq_hz = frequency_mhz * 1e6
        
        skin_depth = 1 / math.sqrt(math.pi * freq_hz * mu0 * sigma)
        
        # 2. Absorption Loss (A = 8.686 * (t / delta)) in dB
        absorption_loss_db = 8.686 * (self.thickness / 1000.0 / skin_depth)
        
        # 3. Residual Internal Field
        # Field_int = Field_ext * 10^(-Loss/20)
        internal_field = field_strength_kv_m * (10 ** (-absorption_loss_db / 20.0))
        
        status = "SURVIVABLE"
        if internal_field > 5.0:
            status = "CRITICAL_FAILURE_LIKELY"
            self.logger.critical(f"EMP PENETRATION CRITICAL: {internal_field:.2f} kV/m internal field.")
        elif internal_field > 1.0:
            status = "SOFT_ERROR_RISK"
            self.logger.warning(f"High internal pulse detected: {internal_field:.2f} kV/m.")

        return {
            "survivability_status": status,
            "absorption_loss_db": round(absorption_loss_db, 2),
            "internal_field_kv_m": round(internal_field, 4),
            "skin_depth_um": round(skin_depth * 1e6, 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    era = EMPAnalyzer()
    print(era.analyze_pulse(field_strength_kv_m=50.0, frequency_mhz=10.0))
