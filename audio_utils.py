import os
import subprocess
from pathlib import Path
import requests
import soundfile as sf

def download_file_from_telegram(token: str, file_path: str, output_path: Path | str, timeout: int = 120) -> bool:
    """
    Download a file from Telegram API using streaming requests.
    More reliable and resilient than aiohttp streaming on Windows.
    """
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        print(f"Error downloading file from Telegram: {e}")
        return False

def convert_to_wav(input_path: Path | str, output_path: Path | str, sample_rate: int = 48000) -> bool:
    """
    Convert any audio file (ogg, mp3, m4a, flac, etc.) to standardized WAV format (mono, 16-bit PCM).
    Uses ffmpeg for high compatibility and speed.
    """
    input_path = str(input_path)
    output_path = str(output_path)

    cmd = [
        "ffmpeg",
        "-y",               # Overwrite output
        "-i", input_path,    # Input file
        "-ac", "1",         # Mono channel
        "-ar", str(sample_rate),  # Sample rate
        "-c:a", "pcm_s16le",# 16-bit PCM
        output_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"Error converting audio to wav: {e}")
        return False

def convert_wav_to_ogg(input_wav: Path | str, output_ogg: Path | str) -> bool:
    """
    Convert WAV audio to OGG/Opus format suitable for Telegram voice messages.
    """
    input_wav = str(input_wav)
    output_ogg = str(output_ogg)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_wav,
        "-c:a", "libopus",
        "-b:a", "64k",
        "-vbr", "on",
        output_ogg
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0 and os.path.exists(output_ogg)
    except Exception as e:
        print(f"Error converting wav to ogg: {e}")
        return False

def get_audio_duration(file_path: Path | str) -> float:
    """
    Get audio duration in seconds using soundfile or ffprobe.
    """
    try:
        info = sf.info(str(file_path))
        return info.duration
    except Exception:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(res.stdout.strip())
        except Exception:
            return 0.0

def validate_audio_voice(file_path: Path | str):
    """
    Validate that voice recording has audio content and acceptable duration.
    Returns: (is_valid: bool, status: str, duration: float, max_amp: float)
    """
    try:
        import numpy as np
        data, sr = sf.read(str(file_path))
        duration = len(data) / sr
        max_amp = float(np.max(np.abs(data)))

        if max_amp < 0.01:
            return False, "SILENT", duration, max_amp
        if duration < 2.5:
            return False, "TOO_SHORT", duration, max_amp
        return True, "OK", duration, max_amp
    except Exception as e:
        return False, str(e), 0.0, 0.0
