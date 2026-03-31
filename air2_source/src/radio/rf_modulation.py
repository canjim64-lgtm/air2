"""
RF Signal Modulator/Demodulator Module
Advanced modulation and demodulation for SDR communication
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math


class ModulationScheme(Enum):
    """Modulation schemes"""
    BPSK = "binary_phase_shift_keying"
    QPSK = "quadrature_phase_shift_keying"
    QAM16 = "quadrature_amplitude_16"
    QAM64 = "quadrature_amplitude_64"
    FSK = "frequency_shift_keying"
    GFSK = "gaussian_frequency_shift_keying"
    OOK = "on_off_keying"
    MSK = "minimum_shift_keying"
    DPSK = "differential_phase_shift_keying"


@dataclass
class ModulatedSignal:
    """Modulated signal output"""
    i_samples: np.ndarray
    q_samples: np.ndarray
    symbol_rate: float
    modulation: ModulationScheme
    bandwidth: float
    constellation: Optional[np.ndarray] = None


class Modulator:
    """Signal modulator for various modulation schemes"""
    
    def __init__(self, symbol_rate: float = 9600, carrier_freq: float = 433.92e6,
                 sample_rate: float = 2.4e6):
        self.symbol_rate = symbol_rate
        self.carrier_freq = carrier_freq
        self.sample_rate = sample_rate
        
        self.samples_per_symbol = int(sample_rate / symbol_rate)
        
    def modulate(self, data: List[int], 
                 scheme: ModulationScheme = ModulationScheme.QPSK) -> ModulatedSignal:
        """Modulate data"""
        
        if scheme == ModulationScheme.BPSK:
            return self._modulate_bpsk(data)
        elif scheme == ModulationScheme.QPSK:
            return self._modulate_qpsk(data)
        elif scheme == ModulationScheme.QAM16:
            return self._modulate_qam(data, 16)
        elif scheme == ModulationScheme.QAM64:
            return self._modulate_qam(data, 64)
        elif scheme == ModulationScheme.FSK:
            return self._modulate_fsk(data)
        elif scheme == ModulationScheme.GFSK:
            return self._modulate_gfsk(data)
        elif scheme == ModulationScheme.OOK:
            return self._modulate_ook(data)
        elif scheme == ModulationScheme.MSK:
            return self._modulate_msk(data)
        else:
            return self._modulate_qpsk(data)
    
    def _modulate_bpsk(self, data: List[int]) -> ModulatedSignal:
        """BPSK modulation"""
        
        # Map bits to symbols (0 -> -1, 1 -> 1)
        symbols = np.array([1 if b else -1 for b in data])
        
        # Create baseband signal
        i_samples = symbols.astype(float)
        q_samples = np.zeros_like(i_samples)
        
        # Upsample
        i_samples = np.repeat(i_samples, self.samples_per_symbol)
        q_samples = np.repeat(q_samples, self.samples_per_symbol)
        
        # Pulse shaping (raised cosine)
        i_samples = self._raised_cosine_filter(i_samples)
        
        # Carrier modulation
        t = np.arange(len(i_samples)) / self.sample_rate
        carrier = np.exp(1j * 2 * np.pi * self.carrier_freq * t)
        
        i_out = i_samples * np.cos(2 * np.pi * self.carrier_freq * t)
        q_out = i_samples * np.sin(2 * np.pi * self.carrier_freq * t)
        
        # Create constellation
        constellation = np.array([-1, 1])
        
        return ModulatedSignal(
            i_samples=i_out,
            q_samples=q_out,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.BPSK,
            bandwidth=self.symbol_rate * 1.5,
            constellation=constellation
        )
    
    def _modulate_qpsk(self, data: List[int]) -> ModulatedSignal:
        """QPSK modulation"""
        
        # Pad to multiple of 2
        if len(data) % 2 != 0:
            data.append(0)
        
        # Map pairs to QPSK symbols
        symbol_map = {
            (0, 0): 1 + 1j,   # 00 -> 1 + j
            (0, 1): -1 + 1j,  # 01 -> -1 + j
            (1, 0): 1 - 1j,   # 10 -> 1 - j
            (1, 1): -1 - 1j   # 11 -> -1 - j
        }
        
        symbols = []
        for i in range(0, len(data), 2):
            bits = (data[i], data[i+1])
            symbols.append(symbol_map.get(bits, 1+1j))
        
        symbols = np.array(symbols) / np.sqrt(2)  # Normalize
        
        # Upsample
        i_samples = np.repeat(symbols.real, self.samples_per_symbol)
        q_samples = np.repeat(symbols.imag, self.samples_per_symbol)
        
        # Pulse shaping
        i_samples = self._raised_cosine_filter(i_samples)
        q_samples = self._raised_cosine_filter(q_samples)
        
        # Carrier modulation
        i_out = i_samples * np.cos(2 * np.pi * self.carrier_freq * 
                                    np.arange(len(i_samples)) / self.sample_rate)
        q_out = q_samples * np.sin(2 * np.pi * self.carrier_freq * 
                                    np.arange(len(q_samples)) / self.sample_rate)
        
        # Constellation
        constellation = np.array([1+1j, -1+1j, 1-1j, -1-1j]) / np.sqrt(2)
        
        return ModulatedSignal(
            i_samples=i_out,
            q_samples=q_out,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.QPSK,
            bandwidth=self.symbol_rate * 1.5,
            constellation=constellation
        )
    
    def _modulate_qam(self, data: List[int], m: int) -> ModulatedSignal:
        """M-QAM modulation"""
        
        # Gray coding for QAM
        bits_per_symbol = int(math.log2(m))
        
        # Pad data
        while len(data) % bits_per_symbol != 0:
            data.append(0)
        
        # Generate QAM constellation
        k = int(math.sqrt(m))
        constellation = []
        
        for i in range(k):
            for j in range(k):
                real = 2 * i - (k - 1)
                imag = 2 * j - (k - 1)
                constellation.append(complex(real, imag))
        
        constellation = np.array(constellation)
        constellation /= np.sqrt(np.mean(np.abs(constellation)**2))
        
        # Map data to symbols
        symbols = []
        for i in range(0, len(data), bits_per_symbol):
            bits = data[i:i+bits_per_symbol]
            idx = int(''.join(map(str, bits)), 2) % m
            symbols.append(constellation[idx] if idx < len(constellation) else 0)
        
        symbols = np.array(symbols)
        
        # Upsample
        i_samples = np.repeat(symbols.real, self.samples_per_symbol)
        q_samples = np.repeat(symbols.imag, self.samples_per_symbol)
        
        # Pulse shaping
        i_samples = self._raised_cosine_filter(i_samples)
        q_samples = self._raised_cosine_filter(q_samples)
        
        # Carrier
        i_out = i_samples * np.cos(2 * np.pi * self.carrier_freq * 
                                    np.arange(len(i_samples)) / self.sample_rate)
        q_out = q_samples * np.sin(2 * np.pi * self.carrier_freq * 
                                    np.arange(len(q_samples)) / self.sample_rate)
        
        return ModulatedSignal(
            i_samples=i_out,
            q_samples=q_out,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.QAM16 if m == 16 else ModulationScheme.QAM64,
            bandwidth=self.symbol_rate * math.log2(m) / 2,
            constellation=constellation
        )
    
    def _modulate_fsk(self, data: List[int]) -> ModulatedSignal:
        """FSK modulation"""
        
        freq_dev = self.symbol_rate / 2  # Frequency deviation
        
        # Generate baseband
        samples = []
        
        for bit in data:
            freq = self.carrier_freq + (freq_dev if bit else -freq_dev)
            t = np.arange(self.samples_per_symbol) / self.sample_rate
            phase = 2 * np.pi * freq * t
            samples.append(np.exp(1j * phase))
        
        samples = np.concatenate(samples)
        
        i_out = samples.real
        q_out = samples.imag
        
        constellation = np.array([
            self.carrier_freq - freq_dev,
            self.carrier_freq + freq_dev
        ])
        
        return ModulatedSignal(
            i_samples=i_out,
            q_samples=q_out,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.FSK,
            bandwidth=freq_dev * 2,
            constellation=constellation
        )
    
    def _modulate_gfsk(self, data: List[int]) -> ModulatedSignal:
        """Gaussian FSK modulation"""
        
        # Gaussian filter
        bt = 0.5  # Bandwidth-time product
        
        # Generate baseband as for FSK
        freq_dev = self.symbol_rate / 2
        samples = []
        
        for bit in data:
            freq = self.carrier_freq + (freq_dev if bit else -freq_dev)
            t = np.arange(self.samples_per_symbol) / self.sample_rate
            phase = 2 * np.pi * freq * t
            
            # Apply Gaussian filter to phase (simplified)
            samples.append(np.exp(1j * phase))
        
        samples = np.concatenate(samples)
        
        return ModulatedSignal(
            i_samples=samples.real,
            q_samples=samples.imag,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.GFSK,
            bandwidth=freq_dev * 2,
            constellation=None
        )
    
    def _modulate_ook(self, data: List[int]) -> ModulatedSignal:
        """On-Off Keying modulation"""
        
        samples = []
        
        for bit in data:
            if bit:
                t = np.arange(self.samples_per_symbol) / self.sample_rate
                carrier = np.cos(2 * np.pi * self.carrier_freq * t)
                samples.append(carrier)
            else:
                samples.append(np.zeros(self.samples_per_symbol))
        
        samples = np.concatenate(samples)
        
        return ModulatedSignal(
            i_samples=samples,
            q_samples=np.zeros_like(samples),
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.OOK,
            bandwidth=self.symbol_rate,
            constellation=np.array([0, 1])
        )
    
    def _modulate_msk(self, data: List[int]) -> ModulatedSignal:
        """Minimum Shift Keying"""
        
        # MSK is continuous phase FSK with freq dev = 1/(2*Ts)
        freq_dev = self.symbol_rate / 2
        
        samples = []
        phase = 0
        
        for bit in data:
            delta_f = freq_dev if bit else -freq_dev
            t = np.arange(self.samples_per_symbol) / self.sample_rate
            phase += 2 * np.pi * delta_f * t
            samples.append(np.exp(1j * phase))
        
        samples = np.concatenate(samples)
        
        return ModulatedSignal(
            i_samples=samples.real,
            q_samples=samples.imag,
            symbol_rate=self.symbol_rate,
            modulation=ModulationScheme.MSK,
            bandwidth=self.symbol_rate * 1.5,
            constellation=None
        )
    
    def _raised_cosine_filter(self, samples: np.ndarray, 
                              rolloff: float = 0.5) -> np.ndarray:
        """Apply raised cosine pulse shaping filter"""
        
        n = len(samples)
        
        # Create filter
        t = np.arange(n) - n / 2
        filter_response = np.sinc(t / self.samples_per_symbol)
        
        # Apply window
        window = np.hanning(n)
        filter_response *= window
        
        # Apply to samples
        filtered = np.convolve(samples, filter_response, mode='same')
        
        return filtered


class Demodulator:
    """Signal demodulator"""
    
    def __init__(self, symbol_rate: float = 9600, carrier_freq: float = 433.92e6,
                 sample_rate: float = 2.4e6):
        self.symbol_rate = symbol_rate
        self.carrier_freq = carrier_freq
        self.sample_rate = sample_rate
        
        self.samples_per_symbol = int(sample_rate / symbol_rate)
        
    def demodulate(self, i_samples: np.ndarray, q_samples: np.ndarray,
                   scheme: ModulationScheme = ModulationScheme.QPSK) -> List[int]:
        """Demodulate signal"""
        
        # Combine to complex
        samples = i_samples + 1j * q_samples
        
        # Downconvert
        t = np.arange(len(samples)) / self.sample_rate
        downconverted = samples * np.exp(-1j * 2 * np.pi * self.carrier_freq * t)
        
        # Matched filter
        filtered = self._matched_filter(downconverted)
        
        # Symbol sampling
        symbols = filtered[::self.samples_per_symbol]
        
        # Decision
        if scheme == ModulationScheme.BPSK:
            return self._decide_bpsk(symbols)
        elif scheme == ModulationScheme.QPSK:
            return self._decide_qpsk(symbols)
        elif scheme in [ModulationScheme.QAM16, ModulationScheme.QAM64]:
            return self._decide_qam(symbols, 16 if scheme == ModulationScheme.QAM16 else 64)
        elif scheme in [ModulationScheme.FSK, ModulationScheme.GFSK]:
            return self._decide_fsk(symbols)
        else:
            return self._decide_qpsk(symbols)
    
    def _matched_filter(self, samples: np.ndarray) -> np.ndarray:
        """Matched filter"""
        return samples  # Simplified
    
    def _decide_bpsk(self, symbols: np.ndarray) -> List[int]:
        """BPSK decision"""
        return [1 if s.real > 0 else 0 for s in symbols]
    
    def _decide_qpsk(self, symbols: np.ndarray) -> List[int]:
        """QPSK decision"""
        bits = []
        
        for s in symbols:
            # Determine quadrant
            if s.real >= 0 and s.imag >= 0:
                bits.extend([0, 0])  # 00
            elif s.real < 0 and s.imag >= 0:
                bits.extend([0, 1])  # 01
            elif s.real >= 0 and s.imag < 0:
                bits.extend([1, 0])  # 10
            else:
                bits.extend([1, 1])  # 11
        
        return bits
    
    def _decide_qam(self, symbols: np.ndarray, m: int) -> List[int]:
        """QAM decision"""
        k = int(math.sqrt(m))
        bits_per_symbol = int(math.log2(m))
        
        # Decision thresholds
        thresholds = np.arange(k) * 2 - (k - 1)
        
        bits = []
        
        for s in symbols:
            # Find nearest constellation point
            real_idx = np.argmin(np.abs(thresholds - s.real))
            imag_idx = np.argmin(np.abs(thresholds - s.imag))
            
            # Convert to bits
            idx = real_idx * k + imag_idx
            bits.extend([int(b) for b in format(idx, f'0{bits_per_symbol}b')])
        
        return bits
    
    def _decide_fsk(self, symbols: np.ndarray) -> List[int]:
        """FSK decision"""
        return [1 if s.real > 0 else 0 for s in symbols]


class OFDMModulator:
    """OFDM modulator"""
    
    def __init__(self, num_subcarriers: int = 64, cyclic_prefix: int = 16,
                 symbol_rate: float = 9600, sample_rate: float = 2.4e6):
        self.num_subcarriers = num_subcarriers
        self.cyclic_prefix = cyclic_prefix
        self.symbol_rate = symbol_rate
        self.sample_rate = sample_rate
        
    def modulate_ofdm(self, data: np.ndarray) -> np.ndarray:
        """Modulate using OFDM"""
        
        # Pad to subcarrier count
        if len(data) < self.num_subcarriers:
            data = np.pad(data, (0, self.num_subcarriers - len(data)))
        
        # IFFT
        ofdm_symbol = np.fft.ifft(data) * self.num_subcarriers
        
        # Add cyclic prefix
        cp = ofdm_symbol[-self.cyclic_prefix:]
        symbol_with_cp = np.concatenate([cp, ofdm_symbol])
        
        return symbol_with_cp
    
    def demodulate_ofdm(self, samples: np.ndarray) -> np.ndarray:
        """Demodulate OFDM"""
        
        # Remove cyclic prefix
        ofdm_symbol = samples[self.cyclic_prefix:]
        
        # FFT
        data = np.fft.fft(ofdm_symbol) / self.num_subcarriers
        
        return data


class SpreadSpectrumModulator:
    """Spread spectrum modulator"""
    
    def __init__(self, spreading_factor: int = 8, 
                 sample_rate: float = 2.4e6):
        self.spreading_factor = spreading_factor
        self.sample_rate = sample_rate
        
        # Generate PN sequence
        self.pn_sequence = self._generate_pn_sequence(127)
        
    def _generate_pn_sequence(self, length: int) -> np.ndarray:
        """Generate PN sequence"""
        # Simple linear feedback shift register
        reg = [1] * 7
        sequence = []
        
        for _ in range(length):
            out = reg[-1]
            sequence.append(out)
            
            # Feedback
            new = (reg[-1] ^ reg[-2]) if length > 2 else 1
            reg = [new] + reg[:-1]
        
        return np.array(sequence)
    
    def modulate_dsss(self, data: List[int]) -> np.ndarray:
        """Direct Sequence Spread Spectrum"""
        
        # Spread each bit
        spread_data = []
        for bit in data:
            if bit:
                spread_data.extend(self.pn_sequence * 2 - 1)
            else:
                spread_data.extend(-(self.pn_sequence * 2 - 1))
        
        return np.array(spread_data)
    
    def demodulate_dsss(self, spread_signal: np.ndarray) -> List[int]:
        """Demodulate DSSS"""
        
        bits = []
        sps = self.spreading_factor * len(self.pn_sequence)
        
        for i in range(0, len(spread_signal), sps):
            segment = spread_signal[i:i+sps]
            
            # Correlate with PN sequence
            corr = np.dot(segment, self.pn_sequence * 2 - 1)
            
            bits.append(1 if corr > 0 else 0)
        
        return bits


# Example usage
if __name__ == "__main__":
    print("Testing RF Modulation/Demodulation...")
    
    # Test Modulator
    print("\n1. Testing Modulator...")
    mod = Modulator(symbol_rate=9600, carrier_freq=433.92e6, sample_rate=2.4e6)
    
    # Test data
    test_data = [1, 0, 1, 1, 0, 0, 1, 0]
    
    # BPSK
    signal = mod.modulate(test_data, ModulationScheme.BPSK)
    print(f"   BPSK: {len(signal.i_samples)} samples")
    
    # QPSK
    signal = mod.modulate(test_data, ModulationScheme.QPSK)
    print(f"   QPSK: {len(signal.i_samples)} samples")
    
    # FSK
    signal = mod.modulate(test_data, ModulationScheme.FSK)
    print(f"   FSK: {len(signal.i_samples)} samples")
    
    # Test Demodulator
    print("\n2. Testing Demodulator...")
    demod = Demodulator(symbol_rate=9600, carrier_freq=433.92e6, sample_rate=2.4e6)
    
    # Get demodulated data
    demod_data = demod.demodulate(signal.i_samples, signal.q_samples, ModulationScheme.FSK)
    print(f"   Demodulated {len(demod_data)} bits")
    
    # Test OFDM
    print("\n3. Testing OFDM...")
    ofdm = OFDMModulator()
    test_symbols = np.random.randn(64) + 1j * np.random.randn(64)
    ofdm_signal = ofdm.modulate_ofdm(test_symbols)
    print(f"   OFDM: {len(ofdm_signal)} samples")
    
    # Test DSSS
    print("\n4. Testing DSSS...")
    dsss = SpreadSpectrumModulator()
    spread = dsss.modulate_dsss([1, 0, 1, 1])
    print(f"   Spread: {len(spread)} chips")
    
    despread = dsss.demodulate_dsss(spread)
    print(f"   Despread: {despread}")
    
    print("\n✅ RF Modulation/Demodulation test completed!")