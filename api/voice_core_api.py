import os
import pickle

from voice_system import VoiceRecognitionSystem, Config
from voice_system.hf_utils import ensure_hf_login, patch_hf_hub_download

patch_hf_hub_download()
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv('HF_TOKEN')
VOICE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'voice_database.pkl')

_config = None
_system = None


def _load_voice_db_safe() -> dict:
    """直接读取声纹数据库文件，不初始化任何 ML 模型"""
    if os.path.exists(VOICE_DB_PATH):
        try:
            with open(VOICE_DB_PATH, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return {}
    return {}


def _save_voice_db_safe(db: dict) -> None:
    """直接写入声纹数据库文件"""
    with open(VOICE_DB_PATH, 'wb') as f:
        pickle.dump(db, f)


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
    """获取声纹库学生名单（仅读磁盘，不加载 ML 模型）"""
    return list(_load_voice_db_safe().keys())


def delete_voice_enrollment(name: str) -> dict:
    """删除声纹录入（优先使用内存中的 voice_system，否则直接操作磁盘）"""
    name = name.strip()
    if not name:
        return {"status": "error", "message": "Name cannot be empty."}

    # 如果 voice system 已初始化，使用它（数据库已在内存中）
    if _system is not None:
        mgr = _system.voiceprint_mgr
        if name not in mgr.database:
            return {"status": "error", "message": f"Student '{name}' not found in voice database."}
        success = mgr.delete_student(name)
        if success:
            return {"status": "success", "message": f"Voice enrollment deleted for {name}."}
        return {"status": "error", "message": f"Failed to delete voice enrollment for {name}."}

    # 否则直接操作磁盘文件
    db = _load_voice_db_safe()
    if name not in db:
        return {"status": "error", "message": f"Student '{name}' not found in voice database."}
    del db[name]
    _save_voice_db_safe(db)
    return {"status": "success", "message": f"Voice enrollment deleted for {name}."}
