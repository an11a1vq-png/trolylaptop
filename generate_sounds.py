import math
import struct
import wave
import os

def generate_cosmic_chime(filename, freqs, durations, sample_rate=44100, volume=0.3):
    """Generate futuristic, clean crystal cosmic chime for NOVA."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    audio_data = bytearray()
    
    for freq, duration in zip(freqs, durations):
        num_samples = int(sample_rate * duration)
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Smooth exponential decay for a crisp futuristic sound
            envelope = math.exp(-4.5 * (t / duration))
            if i < int(sample_rate * 0.01):
                envelope *= (i / (sample_rate * 0.01))

            # Futuristic harmonic shimmer (Fundamental + Octave + 5th harmonic shimmer)
            val = (
                math.sin(2.0 * math.pi * freq * t) * 0.6 +
                math.sin(2.0 * math.pi * (freq * 2.0) * t) * 0.25 +
                math.sin(2.0 * math.pi * (freq * 3.0) * t) * 0.15
            )
            sample = int(val * envelope * volume * 32767.0)
            sample = max(-32768, min(32767, sample))
            audio_data.extend(struct.pack('<h', sample))

    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)        # Mono
        wav_file.setsampwidth(2)       # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    print(f"Generated {filename}")

if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    # NOVA Wake Sound: Crisp Sci-Fi shimmer (E5 659Hz -> B5 987Hz -> E6 1318Hz)
    generate_cosmic_chime(os.path.join(assets_dir, "beep_listen.wav"), [659.25, 987.77, 1318.51], [0.06, 0.06, 0.14], volume=0.32)
    # NOVA Completion Sound: Soft resolve (B5 987Hz -> E5 659Hz)
    generate_cosmic_chime(os.path.join(assets_dir, "beep_done.wav"), [987.77, 659.25], [0.05, 0.12], volume=0.28)
