"""InsightFace 共享逻辑（face_api / face_worker 共用，避免重复加载模型）。"""
import os
import pickle
import numpy as np
from insightface.app import FaceAnalysis

INSIGHTFACE_DIR = "insightface-master"
DATABASE_ROOT = os.path.join(INSIGHTFACE_DIR, "face_database")
VECTORS_FILE = os.path.join(INSIGHTFACE_DIR, "face_vectors.pkl")

_FACE_APP = None
_SAVED_VECTORS = {}


def get_face_app() -> FaceAnalysis:
    global _FACE_APP
    if _FACE_APP is not None:
        return _FACE_APP
    try:
        _FACE_APP = FaceAnalysis(
            name='buffalo_l',
            root=os.path.expanduser('~/.insightface'),
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
        )
        _FACE_APP.prepare(ctx_id=0, det_size=(640, 640))
    except Exception:
        _FACE_APP = FaceAnalysis(name='buffalo_l', root=os.path.expanduser('~/.insightface'))
        _FACE_APP.prepare(ctx_id=-1, det_size=(640, 640))
    return _FACE_APP


def load_saved_vectors() -> dict:
    global _SAVED_VECTORS
    os.makedirs(INSIGHTFACE_DIR, exist_ok=True)
    if os.path.exists(VECTORS_FILE):
        with open(VECTORS_FILE, "rb") as f:
            try:
                _SAVED_VECTORS = pickle.load(f)
            except EOFError:
                _SAVED_VECTORS = {}
    else:
        _SAVED_VECTORS = {}
    return _SAVED_VECTORS


def clear_vectors_cache() -> None:
    global _SAVED_VECTORS
    _SAVED_VECTORS = {}


def save_vector(name: str, vector: np.ndarray) -> None:
    os.makedirs(INSIGHTFACE_DIR, exist_ok=True)
    vectors = load_saved_vectors()
    vectors[name] = vector
    with open(VECTORS_FILE, "wb") as f:
        pickle.dump(vectors, f)


def match_face(embedding, threshold: float = 0.4) -> str:
    vectors = load_saved_vectors()
    if not vectors:
        return "未知人物"
    best_name = "未知人物"
    best_sim = threshold
    for name, saved_vector in vectors.items():
        if isinstance(saved_vector, list):
            saved_vector = np.array(saved_vector)
        sim = np.dot(saved_vector, embedding) / (
            np.linalg.norm(saved_vector) * np.linalg.norm(embedding)
        )
        if sim > best_sim:
            best_sim = sim
            best_name = name
    return best_name
