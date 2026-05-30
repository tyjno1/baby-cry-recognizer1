# -*- coding: utf-8 -*-
"""
Android Audio Recorder for Kivy
Uses pyjnius to access Android AudioRecord API
"""
import numpy as np

try:
    from jnius import autoclass, PythonJavaClass, java_method
    HAS_JNIUS = True
except ImportError:
    HAS_JNIUS = False

SAMPLE_RATE = 16000
DURATION = 5


class AndroidAudioRecorder:
    """Record audio on Android using AudioRecord API"""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.recording = False

    def record(self, duration=DURATION):
        """Record audio for given duration, returns numpy array"""
        if not HAS_JNIUS:
            # Fallback: return mock audio for testing
            print("[WARNING] pyjnius not available, using mock audio")
            return np.random.randn(duration * self.sample_rate).astype(np.float32) * 0.1

        try:
            AudioRecord = autoclass("android.media.AudioRecord")
            AudioFormat = autoclass("android.media.AudioFormat")
            MediaRecorder = autoclass("android.media.MediaRecorder")

            buffer_size = AudioRecord.getMinBufferSize(
                self.sample_rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )

            if buffer_size < 2048:
                buffer_size = 2048

            recorder = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                self.sample_rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                buffer_size * 2
            )

            if recorder.getState() != AudioRecord.STATE_INITIALIZED:
                print("[ERROR] AudioRecord failed to initialize")
                return np.random.randn(duration * self.sample_rate).astype(np.float32) * 0.1

            recorder.startRecording()
            self.recording = True

            total_samples = duration * self.sample_rate
            all_data = bytearray()
            shorts_per_read = buffer_size // 2

            while len(all_data) < total_samples * 2:
                buffer = bytearray(buffer_size)
                read = recorder.read(buffer, 0, buffer_size)
                if read > 0:
                    all_data.extend(buffer[:read])
                else:
                    break

            recorder.stop()
            recorder.release()
            self.recording = False

            # Convert PCM 16-bit to float32
            audio_data = np.frombuffer(bytes(all_data[:total_samples * 2]), dtype=np.int16)
            audio_float = audio_data.astype(np.float32) / 32768.0

            return audio_float

        except Exception as e:
            print(f"[ERROR] Audio recording failed: {e}")
            return np.random.randn(duration * self.sample_rate).astype(np.float32) * 0.1


# Fallback: try sounddevice on desktop
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


def record_audio_mobile(duration=DURATION, sample_rate=SAMPLE_RATE):
    """Cross-platform audio recording"""
    if HAS_SOUNDDEVICE:
        print(f"[INFO] Recording {duration}s audio via sounddevice...")
        audio = sd.rec(int(duration * sample_rate),
                       samplerate=sample_rate,
                       channels=1,
                       dtype=np.float32)
        sd.wait()
        return audio.flatten()
    elif HAS_JNIUS:
        recorder = AndroidAudioRecorder(sample_rate)
        return recorder.record(duration)
    else:
        print("[INFO] Using mock audio (no recording device)")
        return np.random.randn(duration * sample_rate).astype(np.float32) * 0.1
