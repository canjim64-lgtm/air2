"""
In-Situ Resource Utilization (ISRU) Analyzer for AirOne Professional v4.0
Models chemical yields for Martian/Lunar atmospheric processing and soil electrolysis.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ISRUAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ISRU")
        # Molar masses (g/mol)
        self.mm = {"CO2": 44.01, "H2": 2.016, "CH4": 16.04, "H2O": 18.015, "O2": 31.99}
        self.logger.info("ISRU Chemical Yield Analyzer Initialized.")

    def analyze_sabatier_process(self, co2_input_kg: float, h2_input_kg: float, efficiency: float = 0.9) -> Dict[str, Any]:
        """
        Calculates methane and water yield from Sabatier reaction.
        Reaction: CO2 + 4H2 -> CH4 + 2H2O
        """
        # Calculate moles of reactants
        moles_co2 = (co2_input_kg * 1000.0) / self.mm["CO2"]
        moles_h2 = (h2_input_kg * 1000.0) / self.mm["H2"]
        
        # Determine limiting reactant (requires 4 moles H2 per 1 mole CO2)
        stoich_h2_needed = moles_co2 * 4
        
        if moles_h2 >= stoich_h2_needed:
            # CO2 is limiting
            actual_moles_ch4 = moles_co2 * efficiency
            actual_moles_h2o = (moles_co2 * 2) * efficiency
            remaining_h2_kg = ((moles_h2 - stoich_h2_needed) * self.mm["H2"]) / 1000.0
            limiting = "CO2"
        else:
            # H2 is limiting
            actual_moles_ch4 = (moles_h2 / 4) * efficiency
            actual_moles_h2o = (moles_h2 / 2) * efficiency
            remaining_h2_kg = 0.0
            limiting = "H2"

        yield_ch4_kg = (actual_moles_ch4 * self.mm["CH4"]) / 1000.0
        yield_h2o_kg = (actual_moles_h2o * self.mm["H2O"]) / 1000.0

        return {
            "reaction": "Sabatier (CH4 Synthesis)",
            "limiting_reactant": limiting,
            "methane_yield_kg": round(yield_ch4_kg, 3),
            "water_yield_kg": round(yield_h2o_kg, 3),
            "efficiency_applied": efficiency,
            "oxygen_potential_from_water_kg": round((yield_h2o_kg * (self.mm["O2"] / (2 * self.mm["H2O"]))), 3)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    isru = ISRUAnalyzer()
    print(isru.analyze_sabatier_process(co2_input_kg=10.0, h2_input_kg=2.0))
