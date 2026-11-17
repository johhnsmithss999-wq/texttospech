import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
TEMP_DIR = DATA_DIR / "temp"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# VoxCPM Settings
VOXCPM_MODEL_ID = os.getenv("VOXCPM_MODEL_ID", "openbmb/VoxCPM2")
DEVICE = os.getenv("VOXCPM_DEVICE", "cuda")  # "cuda" or "cpu"
LOAD_DENOISER = os.getenv("VOXCPM_LOAD_DENOISER", "false").lower() in ("true", "1", "yes")

# Default generation parameters
DEFAULT_CFG_VALUE = float(os.getenv("DEFAULT_CFG_VALUE", "2.0"))
DEFAULT_INFERENCE_TIMESTEPS = int(os.getenv("DEFAULT_INFERENCE_TIMESTEPS", "6"))
