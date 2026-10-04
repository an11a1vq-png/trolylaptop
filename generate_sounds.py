import math
import struct
import wave
import os

def generate_chime(filename, freqs, durations, sample_rate=44100, volume=0.3):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    audio_data = bytearray()
    
    for freq, duration in zip(freqs, durations):
        num_samples = int(sample_rate * duration)
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Apply smooth envelope (attack and decay) to avoid clicks
            envelope = 1.0
            attack_samples = int(sample_rate * 0.015)
            decay_samples = int(sample_rate * 0.05)
            if i < attack_samples:
                envelope = i / attack_samples
            elif i > num_samples - decay_samples:
                envelope = (num_samples - i) / decay_samples

            # Dual harmonic for a warm bell/chime sound
            val = math.sin(2.0 * math.pi * freq * t) * 0.7 + math.sin(2.0 * math.pi * (freq * 2) * t) * 0.3
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
    # Friendly "Hey Google" listening chime (Ascending C5 -> E5 -> G5)
    generate_chime(os.path.join(assets_dir, "beep_listen.wav"), [523.25, 659.25, 783.99], [0.08, 0.08, 0.14], volume=0.35)
    # Completion chime (Soft G5 -> C5)
    generate_chime(os.path.join(assets_dir, "beep_done.wav"), [783.99, 523.25], [0.07, 0.12], volume=0.3)
