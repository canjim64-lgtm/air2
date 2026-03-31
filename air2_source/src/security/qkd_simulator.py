"""
Quantum Key Distribution (QKD) BB84 Simulator for AirOne Professional v4.0
Simulates the BB84 protocol for secure cryptographic key exchange between Ground Station and CanSat.
"""
import logging
import random
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class QKDSimulator:
    def __init__(self, key_length: int = 256):
        self.logger = logging.getLogger(f"{__name__}.QKDSimulator")
        self.target_key_length = key_length
        self.bases = ['+', 'x'] # Rectilinear (+), Diagonal (x)
        self.logger.info(f"QKD BB84 Simulator Initialized (Target Key: {key_length} bits).")

    def _generate_random_bits(self, length: int) -> List[int]:
        return [random.choice([0, 1]) for _ in range(length)]

    def _generate_random_bases(self, length: int) -> List[str]:
        return [random.choice(self.bases) for _ in range(length)]

    def _encode_photons(self, bits: List[int], bases: List[str]) -> List[str]:
        """Simulates Alice encoding bits into photon polarization states."""
        photons = []
        for bit, basis in zip(bits, bases):
            if basis == '+':
                photons.append('|' if bit == 1 else '-')
            else: # basis == 'x'
                photons.append('/' if bit == 1 else '')
        return photons

    def _measure_photons(self, photons: List[str], bases: List[str], intercept_rate: float = 0.0) -> List[int]:
        """Simulates Bob (or Eve) measuring photons with their chosen bases."""
        measurements = []
        for photon, basis in zip(photons, bases):
            # Simulate environment noise / interception
            if random.random() < intercept_rate:
                # Eavesdropper forces a state collapse, destroying original polarization
                photon = random.choice(['|', '-', '/', ''])

            if basis == '+':
                if photon in ['|', '-']:
                    measurements.append(1 if photon == '|' else 0)
                else: # Wrong basis, random result
                    measurements.append(random.choice([0, 1]))
            else: # basis == 'x'
                if photon in ['/', '']:
                    measurements.append(1 if photon == '/' else 0)
                else: # Wrong basis, random result
                    measurements.append(random.choice([0, 1]))
        return measurements

    def simulate_key_exchange(self, eavesdropper_presence: float = 0.0) -> Dict[str, Any]:
        """Executes a full BB84 protocol sequence."""
        # 1. Alice generates bits and bases
        num_photons = self.target_key_length * 4 # Oversample to account for basis mismatch
        alice_bits = self._generate_random_bits(num_photons)
        alice_bases = self._generate_random_bases(num_photons)
        
        # 2. Alice encodes and transmits
        photons = self._encode_photons(alice_bits, alice_bases)
        
        # 3. Bob generates bases and measures
        bob_bases = self._generate_random_bases(num_photons)
        bob_measurements = self._measure_photons(photons, bob_bases, intercept_rate=eavesdropper_presence)
        
        # 4. Reconciliation (Public channel basis comparison)
        sifted_key = []
        for i in range(num_photons):
            if alice_bases[i] == bob_bases[i]:
                sifted_key.append(bob_measurements[i])
                
        # 5. Quantum Bit Error Rate (QBER) Check (Subset sacrifice)
        subset_size = min(len(sifted_key) // 4, 128)
        if subset_size == 0: return {"status": "FAILED", "reason": "Insufficient matching bases"}
        
        errors = sum(1 for i in range(subset_size) if sifted_key[i] != alice_bits[i]) # Comparing against Alice's original bits
        qber = errors / subset_size
        
        # Security threshold (typically ~11% for BB84)
        status = "SECURE_KEY_ESTABLISHED"
        if qber > 0.11:
            status = "EAVESDROPPER_DETECTED"
            self.logger.critical(f"QKD COMPROMISED: QBER is {qber*100:.2f}%. Eve detected in channel!")
            return {"status": status, "qber": qber, "key": None}

        # Final key derivation
        final_key = sifted_key[subset_size:subset_size + self.target_key_length]
        if len(final_key) < self.target_key_length:
            return {"status": "FAILED", "reason": "Key too short after sifting"}
            
        hex_key = hex(int("".join(map(str, final_key)), 2))[2:].zfill(self.target_key_length // 4)

        return {
            "status": status,
            "qber": round(qber, 4),
            "photons_transmitted": num_photons,
            "sifted_key_length": len(sifted_key),
            "final_key_hex": hex_key
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    qkd = QKDSimulator()
    print("Clean Channel:")
    print(qkd.simulate_key_exchange(eavesdropper_presence=0.0))
    print("\nCompromised Channel:")
    print(qkd.simulate_key_exchange(eavesdropper_presence=0.2))
