import os
from voice_system import VoiceRecognitionSystem, Config
from voice_system.hf_utils import ensure_hf_login, patch_hf_hub_download

patch_hf_hub_download()
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv('HF_TOKEN')

_config = None
_system = None


def get_voice_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
        _config.setup_directories()
    return _config


def get_voice_system() -> VoiceRecognitionSystem:
    global _system
    if _system is None:
        if not HF_TOKEN:
            raise ValueError("Missing HF_TOKEN environment variable.")
        ensure_hf_login(HF_TOKEN)
        _system = VoiceRecognitionSystem(hf_token=HF_TOKEN, config=get_voice_config())
    return _system


def enroll_voice_data(name: str, audio_path: str) -> dict:
    name = name.strip()
    if not name:
        return {"status": "error", "message": "Name cannot be empty."}
    if not os.path.exists(audio_path):
        return {"status": "error", "message": f"Audio file not found: {audio_path}"}

    try:
        success = get_voice_system().voiceprint_mgr.enroll_student(name, audio_path)
        if success:
            return {"status": "success", "message": f"Voiceprint enrolled for {name}."}
        return {"status": "error", "message": f"Enrollment failed for {name}."}
    except Exception as e:
        return {"status": "error", "message": f"Exception: {str(e)}"}


def get_all_enrolled_names() -> list:
    return list(get_voice_system().voiceprint_mgr.database.keys())
