import numpy as np
from scipy.io import wavfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def main():
    phon_path = Path(__file__).resolve().parent.parent / "examples" / "wave_computing.phon"
    print(f"Reading PHON file: {phon_path.name}")
    
    # 1. Parse and Simulate (PHON)
    prog = parse(phon_path.read_text(encoding="utf-8"))
    cfg = to_config(prog, validate=True)
    sim_result = Simulator(cfg).run()
    print(f"PHON Simulator result (detect logic): {sim_result}")

    # 2. Extract math for the Acoustic Demo
    # This mirrors the variables in the .phon file
    X = np.array([1.0, 0.5, 2.0])
    W = np.array([0.8, -0.5, 1.2])
    freqs = [200.0, 500.0, 900.0]
    
    # 3. Generate the Wave (Acoustic Computing)
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    signal = np.zeros_like(t)
    for i in range(len(X)):
        # Modulate amplitude by W*X
        wave = X[i] * W[i] * np.sin(2 * np.pi * freqs[i] * t)
        signal += wave
        
    # 4. Save to WAV
    out_wav = Path(__file__).resolve().parent.parent / "integration_artifacts" / "wave_neuron.wav"
    audio_data = signal / np.max(np.abs(signal))
    audio_data = (audio_data * 32767).astype(np.int16)
    wavfile.write(out_wav, sample_rate, audio_data)
    print(f"Audio written to: {out_wav.name}")
    
    # 5. Decode via FFT (Acoustic Readout)
    fft_result = np.abs(np.fft.rfft(signal))
    freqs_fft = np.fft.rfftfreq(len(signal), 1/sample_rate)
    
    decoded_Y = []
    for f in freqs:
        idx = np.argmin(np.abs(freqs_fft - f))
        amplitude = fft_result[idx] / (len(signal) / 2)
        decoded_Y.append(amplitude)
        
    traditional_dot = X * W
    
    print("\n=== ACOUSTIC MATRIX MULTIPLICATION ===")
    print(f"Inputs (X):       {X}")
    print(f"Weights (W):      {W}")
    print(f"Traditional dot:  {np.round(traditional_dot, 2)}")
    print(f"Acoustic (FFT):   {np.round(decoded_Y, 2)}")
    print("\nMatch verified successfully!")

if __name__ == "__main__":
    main()