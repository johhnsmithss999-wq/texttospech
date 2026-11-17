import json
from pathlib import Path
from typing import Optional, Dict, Any
from config import USERS_DIR, DEFAULT_CFG_VALUE, DEFAULT_INFERENCE_TIMESTEPS

class UserManager:
    @staticmethod
    def get_user_dir(user_id: int | str) -> Path:
        user_dir = USERS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @staticmethod
    def get_voice_path(user_id: int | str) -> Path:
        return UserManager.get_user_dir(user_id) / "voice.wav"

    @staticmethod
    def get_voice_preview_path(user_id: int | str) -> Path:
        return UserManager.get_user_dir(user_id) / "voice.ogg"

    @staticmethod
    def get_profile_file(user_id: int | str) -> Path:
        return UserManager.get_user_dir(user_id) / "profile.json"

    @classmethod
    def has_voice(cls, user_id: int | str) -> bool:
        return cls.get_voice_path(user_id).exists()

    @classmethod
    def get_settings(cls, user_id: int | str) -> Dict[str, Any]:
        profile_file = cls.get_profile_file(user_id)
        default_settings = {
            "cfg_value": DEFAULT_CFG_VALUE,
            "inference_timesteps": DEFAULT_INFERENCE_TIMESTEPS,
            "prompt_text": None,
            "denoise": False
        }
        if profile_file.exists():
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_settings.update(data)
            except Exception as e:
                print(f"Error reading profile for {user_id}: {e}")
        return default_settings

    @classmethod
    def save_settings(cls, user_id: int | str, settings: Dict[str, Any]) -> None:
        profile_file = cls.get_profile_file(user_id)
        current = cls.get_settings(user_id)
        current.update(settings)
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)

    @classmethod
    def delete_voice(cls, user_id: int | str) -> bool:
        voice_path = cls.get_voice_path(user_id)
        preview_path = cls.get_voice_preview_path(user_id)
        deleted = False
        if voice_path.exists():
            voice_path.unlink()
            deleted = True
        if preview_path.exists():
            preview_path.unlink()
        
        settings = cls.get_settings(user_id)
        settings["prompt_text"] = None
        cls.save_settings(user_id, settings)
        return deleted
