# -*- coding: utf-8 -*-
"""音频采集与特征提取（简化版，不依赖librosa和sounddevice）"""
import numpy as np
import wave
import struct
import tempfile
import os

# 尝试导入音频库，如果失败则使用简化实现
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    print("[WARNING] sounddevice not available, using mock audio")

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    print("[WARNING] librosa not available, using simplified features")

from config import SAMPLE_RATE, DURATION, N_MFCC

def record_audio(duration: int = DURATION, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """录制音频"""
    if HAS_SOUNDDEVICE:
        print(f"[INFO] Recording {duration}s audio...")
        audio = sd.rec(int(duration * sample_rate), 
                       samplerate=sample_rate, 
                       channels=1, 
                       dtype=np.float32)
        sd.wait()
        print("[OK] Recording complete")
        return audio.flatten()
    else:
        # 模拟音频数据（用于测试）
        print("[INFO] Using mock audio (no microphone)")
        return np.random.randn(duration * sample_rate).astype(np.float32) * 0.1

def _extract_features_numpy(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict:
    """使用numpy提取简化特征（不依赖librosa）"""
    # 确保音频长度足够
    if len(audio) < sample_rate:
        audio = np.pad(audio, (0, sample_rate - len(audio)), mode='constant')
    
    # 基础统计特征
    mean_amp = np.mean(audio)
    std_amp = np.std(audio)
    max_amp = np.max(audio)
    min_amp = np.min(audio)
    
    # 过零率（简化版）
    zero_crossings = np.sum(np.diff(np.sign(audio)) != 0)
    zcr = zero_crossings / len(audio)
    
    # 能量
    rms = np.sqrt(np.mean(audio ** 2))
    
    # 频谱特征（使用FFT简化版）
    fft = np.fft.fft(audio[:sample_rate])
    freqs = np.fft.fftfreq(sample_rate, 1/sample_rate)
    magnitude = np.abs(fft)
    
    # 频谱质心（简化）
    positive_freqs = freqs[:len(freqs)//2]
    positive_magnitude = magnitude[:len(magnitude)//2]
    spectral_centroid = np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude) if np.sum(positive_magnitude) > 0 else 0
    
    # 频谱rolloff（80%能量点）
    cumsum = np.cumsum(positive_magnitude)
    rolloff_idx = np.searchsorted(cumsum, 0.8 * cumsum[-1]) if cumsum[-1] > 0 else 0
    rolloff = positive_freqs[min(rolloff_idx, len(positive_freqs)-1)]
    
    # 基频估计（简化：找最大幅值频率）
    f0 = positive_freqs[np.argmax(positive_magnitude)] if len(positive_freqs) > 0 else 0
    
    # 模拟MFCC特征（简化版）
    mfcc_mean = np.array([mean_amp, std_amp, max_amp, min_amp, zcr, rms, spectral_centroid/1000, rolloff/1000, f0/100])
    mfcc_std = np.ones_like(mfcc_mean) * std_amp
    
    # 组合特征向量
    feature_vector = np.concatenate([
        mfcc_mean,
        mfcc_std,
        [zcr, f0, 0, spectral_centroid, rolloff, rms]
    ])
    
    return {
        "feature_vector": feature_vector,
        "mfcc_mean": mfcc_mean.tolist(),
        "mfcc_std": mfcc_std.tolist(),
        "zcr": float(zcr),
        "f0_mean": float(f0),
        "f0_std": float(0),
        "spectral_centroid": float(spectral_centroid),
        "rolloff": float(rolloff),
        "rms": float(rms),
        "duration": len(audio) / sample_rate
    }

def _extract_features_librosa(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict:
    """使用librosa提取完整特征"""
    # 确保音频长度足够
    if len(audio) < sample_rate:
        audio = np.pad(audio, (0, sample_rate - len(audio)), mode='constant')
    
    # MFCC特征
    mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)
    
    # 过零率
    zcr = librosa.feature.zero_crossing_rate(audio)
    zcr_mean = np.mean(zcr)
    
    # 基频（F0）
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio, 
        fmin=librosa.note_to_hz('C2'), 
        fmax=librosa.note_to_hz('C7')
    )
    f0_mean = np.nanmean(f0) if np.any(~np.isnan(f0)) else 0
    f0_std = np.nanstd(f0) if np.any(~np.isnan(f0)) else 0
    
    # 频谱质心
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)
    centroid_mean = np.mean(spectral_centroid)
    
    # 频谱 rolloff
    rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)
    rolloff_mean = np.mean(rolloff)
    
    # 能量/RMS
    rms = librosa.feature.rms(y=audio)
    rms_mean = np.mean(rms)
    
    # 组合特征向量
    feature_vector = np.concatenate([
        mfcc_mean,
        mfcc_std,
        [zcr_mean, f0_mean, f0_std, centroid_mean, rolloff_mean, rms_mean]
    ])
    
    return {
        "feature_vector": feature_vector,
        "mfcc_mean": mfcc_mean.tolist(),
        "mfcc_std": mfcc_std.tolist(),
        "zcr": float(zcr_mean),
        "f0_mean": float(f0_mean),
        "f0_std": float(f0_std),
        "spectral_centroid": float(centroid_mean),
        "rolloff": float(rolloff_mean),
        "rms": float(rms_mean),
        "duration": len(audio) / sample_rate
    }

def extract_features(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict:
    """提取音频特征（自动选择实现）"""
    if HAS_LIBROSA:
        return _extract_features_librosa(audio, sample_rate)
    else:
        return _extract_features_numpy(audio, sample_rate)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """计算余弦相似度"""
    if len(v1) != len(v2):
        return 0.0
    
    # 处理零向量
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(v1, v2) / (norm1 * norm2)

def find_best_match(feature_vector: np.ndarray, history: list, threshold: float = 0.85) -> tuple:
    """
    在历史记录中查找最佳匹配
    返回: (是否匹配, 匹配的需求类别, 相似度)
    """
    if not history:
        return False, None, 0.0
    
    best_similarity = 0.0
    best_need = None
    
    for record in history:
        hist_vector = record["feature_vector"]
        similarity = cosine_similarity(feature_vector, hist_vector)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_need = record["actual_need"]
    
    if best_similarity >= threshold:
        return True, best_need, best_similarity
    
    return False, None, best_similarity

def generate_feature_description(features: dict) -> str:
    """生成特征文字描述，用于DeepSeek API"""
    desc = f"""婴儿哭声音频特征分析：
- 音频时长: {features['duration']:.2f}秒
- MFCC均值: {', '.join([f'{x:.2f}' for x in features['mfcc_mean']])}
- 过零率: {features['zcr']:.4f}
- 基频均值: {features['f0_mean']:.2f} Hz
- 基频标准差: {features['f0_std']:.2f}
- 频谱质心: {features['spectral_centroid']:.2f}
- 频谱rolloff: {features['rolloff']:.2f}
- RMS能量: {features['rms']:.4f}
"""
    return desc
