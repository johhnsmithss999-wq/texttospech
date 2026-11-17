import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import asyncio
import threading
import uuid
from pathlib import Path
from typing import Optional, Tuple
import torch
import soundfile as sf
from voxcpm import VoxCPM

from config import (
    VOXCPM_MODEL_ID,
    DEVICE,
    LOAD_DENOISER,
    TEMP_DIR
)
from audio_utils import convert_wav_to_ogg

class TTSEngine:
    _instance: Optional["TTSEngine"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.model: Optional[VoxCPM] = None
        self.sample_rate: int = 48000
        self.is_loaded = False
        self._infer_lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "TTSEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def load_model(self):
        """Loads the VoxCPM2 model into memory."""
        if self.is_loaded:
            return

        chosen_device = DEVICE
        if chosen_device == "cuda" and not torch.cuda.is_available():
            print("[TTSEngine] CUDA requested but not available. Falling back to CPU.")
            chosen_device = "cpu"

        print(f"[TTSEngine] Loading {VOXCPM_MODEL_ID} on {chosen_device} (load_denoiser={LOAD_DENOISER})...")
        try:
            self.model = VoxCPM.from_pretrained(
                hf_model_id=VOXCPM_MODEL_ID,
                load_denoiser=LOAD_DENOISER,
                optimize=False,
                device=chosen_device
            )
            if hasattr(self.model, "tts_model") and hasattr(self.model.tts_model, "sample_rate"):
                self.sample_rate = self.model.tts_model.sample_rate
            else:
                self.sample_rate = 48000
            self.is_loaded = True
            print(f"[TTSEngine] VoxCPM2 model loaded successfully! Sample rate: {self.sample_rate}Hz")
        except Exception as e:
            print(f"[TTSEngine] Failed to load VoxCPM model: {e}")
            raise e

    def _sync_generate(
        self,
        text: str,
        reference_wav_path: Optional[str] = None,
        prompt_wav_path: Optional[str] = None,
        prompt_text: Optional[str] = None,
        cfg_value: float = 2.0,
        inference_timesteps: int = 6,
        denoise: bool = False
    ) -> Tuple[Path, Path]:
        """
        Synchronous speech generation via VoxCPM2.
        Returns: (output_wav_path, output_ogg_path)
        """
        if not self.is_loaded or self.model is None:
            self.load_model()

        computed_max_len = min(max(50, len(text) * 4 + 30), 200)

        kwargs = {
            "text": text,
            "cfg_value": cfg_value,
            "inference_timesteps": inference_timesteps,
            "max_len": computed_max_len,
            "denoise": denoise
        }

        if prompt_wav_path and prompt_text:
            kwargs["prompt_wav_path"] = str(prompt_wav_path)
            kwargs["prompt_text"] = prompt_text
            if reference_wav_path and os.path.exists(reference_wav_path):
                kwargs["reference_wav_path"] = str(reference_wav_path)
        elif reference_wav_path and os.path.exists(reference_wav_path):
            kwargs["reference_wav_path"] = str(reference_wav_path)

        wav = self.model.generate(**kwargs)

        job_id = uuid.uuid4().hex
        out_wav = TEMP_DIR / f"{job_id}.wav"
        out_ogg = TEMP_DIR / f"{job_id}.ogg"

        sf.write(str(out_wav), wav, self.sample_rate)
        convert_wav_to_ogg(out_wav, out_ogg)

        return out_wav, out_ogg

    async def generate_speech(
        self,
        text: str,
        reference_wav_path: Optional[str] = None,
        prompt_wav_path: Optional[str] = None,
        prompt_text: Optional[str] = None,
        cfg_value: float = 2.0,
        inference_timesteps: int = 6,
        denoise: bool = False
    ) -> Tuple[Path, Path]:
        """
        Async thread-safe speech generation.
        """
        async with self._infer_lock:
            return await asyncio.to_thread(
                self._sync_generate,
                text=text,
                reference_wav_path=reference_wav_path,
                prompt_wav_path=prompt_wav_path,
                prompt_text=prompt_text,
                cfg_value=cfg_value,
                inference_timesteps=inference_timesteps,
                denoise=denoise
            )
