import numpy as np
from pydub import AudioSegment
from scipy import signal

from ym_bot.logger import logger


class AudioEffects:
    @staticmethod
    def apply_slow(audio, factor=0.8):
        return audio._spawn(audio.raw_data, overrides={'frame_rate': int(audio.frame_rate * factor)}).set_frame_rate(audio.frame_rate)

    @staticmethod
    def apply_speed(audio, factor=1.25):
        return audio._spawn(audio.raw_data, overrides={'frame_rate': int(audio.frame_rate * factor)}).set_frame_rate(audio.frame_rate)

    @staticmethod
    def apply_bass_boost(audio, gain=10):
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        channels, sr = audio.channels, audio.frame_rate
        b, a = signal.butter(2, min(100 / (sr / 2), 0.99), btype='low')
        gl = 10 ** (gain / 20)
        if channels == 2:
            samples = samples.reshape((-1, 2))
            if len(samples) > 12:
                samples[:, 0] = np.clip(samples[:, 0] + signal.lfilter(b, a, samples[:, 0]) * (gl - 1), -32768, 32767)
                samples[:, 1] = np.clip(samples[:, 1] + signal.lfilter(b, a, samples[:, 1]) * (gl - 1), -32768, 32767)
            samples = samples.flatten()
        elif len(samples) > 12:
            samples = np.clip(samples + signal.lfilter(b, a, samples) * (gl - 1), -32768, 32767)
        return audio._spawn(samples.astype(np.int16).tobytes())

    @staticmethod
    def apply_reverb(audio, decay=0.5, delay_ms=50):
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        output = samples.copy()
        for i in range(2):
            cd, cdec = int(audio.frame_rate * delay_ms / 1000) * (i + 1), decay ** (i + 1)
            if cd < len(output):
                output[cd:] += samples[:-cd] * cdec
        output = np.clip(output, -32768, 32767)
        if audio.channels == 2:
            output = output.flatten()
        return audio._spawn(output.astype(np.int16).tobytes())

    @staticmethod
    def apply_nightcore(audio):
        return AudioEffects.apply_speed(audio, 1.25)

    @staticmethod
    def apply_vaporwave(audio):
        return AudioEffects.apply_reverb(AudioEffects.apply_slow(audio, 0.85), decay=0.3, delay_ms=60)

    @classmethod
    def apply_effect(cls, input_path, effect_name):
        try:
            audio = AudioSegment.from_mp3(input_path)
            effects = {'slow': cls.apply_slow, 'speed': cls.apply_speed, 'bass': cls.apply_bass_boost, 'reverb': cls.apply_reverb, 'nightcore': cls.apply_nightcore, 'vaporwave': cls.apply_vaporwave}
            if effect_name not in effects:
                return input_path
            output_path = input_path.replace('.mp3', f'_{effect_name}.mp3')
            effects[effect_name](audio).export(output_path, format='mp3', bitrate='192k')
            return output_path
        except Exception as e:
            logger.error(f"Effect error: {e}")
            return input_path
