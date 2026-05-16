import os
import pickle
import time
import shutil
import glob
import numpy as np
import cv2
from PIL import Image
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from face_common import (
    DATABASE_ROOT, VECTORS_FILE, get_face_app,
    load_saved_vectors, save_vector, clear_vectors_cache,
)
from api.voice_core_api import get_all_enrolled_names, delete_voice_enrollment

face_bp = Blueprint('face_api', __name__, url_prefix='/api/face')
UPLOAD_FOLDER = 'uploads'


def register_face_data_logic(image_path: str, name: str) -> dict:
    name = name.strip()
    if not name:
        return {"status": "error", "message": "Name cannot be empty.", "code": 400}
    if not os.path.exists(image_path):
        return {"status": "error", "message": f"File not found: {image_path}", "code": 404}

    try:
        img_pil = Image.open(image_path).convert('RGB')
        img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        faces = get_face_app().get(img_bgr)

        if not faces:
            return {"status": "error", "message": "No face detected.", "code": 400}

        face = faces[0]
        face_vector = face.embedding

        person_dir = os.path.join(DATABASE_ROOT, name)
        os.makedirs(person_dir, exist_ok=True)

        x1, y1, x2, y2 = face.bbox.astype(np.int32)
        cropped_face = img_pil.crop((x1, y1, x2, y2))
        filepath = os.path.join(person_dir, f"{name}_{int(time.time())}.jpg")
        cropped_face.save(filepath)

        save_vector(name, face_vector)

        return {
            "status": "success",
            "message": f"Face features enrolled for {name}.",
            "name": name,
            "vector_shape": list(face_vector.shape),
            "code": 200,
        }
    except Exception as e:
        return {"status": "error", "message": f"Exception: {e}", "code": 500}


def get_all_face_enrolled_names() -> list:
    try:
        return list(load_saved_vectors().keys())
    except Exception:
        return []


def get_all_unified_enrolled_names() -> list:
    voice_names = set(get_all_enrolled_names())
    face_names = set(get_all_face_enrolled_names())
    unified = []

    for name in sorted(voice_names | face_names):
        has_voice = name in voice_names
        has_face = name in face_names
        if has_voice and has_face:
            status = 'both'
        elif has_voice:
            status = 'voice'
        elif has_face:
            status = 'face'
        else:
            status = 'none'
        unified.append({"name": name, "enrollment": status})
    return unified


@face_bp.route('/enroll', methods=['POST'])
def enroll_face():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Missing image file"}), 400
    if 'name' not in request.form:
        return jsonify({"status": "error", "message": "Missing name parameter"}), 400

    file = request.files['file']
    name = request.form['name']
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    temp_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(temp_path)

    result = register_face_data_logic(temp_path, name)
    os.remove(temp_path)
    return jsonify({k: v for k, v in result.items() if k != 'code'}), result.get('code', 500)


@face_bp.route('/names', methods=['GET'])
def list_names():
    try:
        return jsonify({"status": "success", "names": get_all_face_enrolled_names()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Query failed: {e}"}), 500


@face_bp.route('/unified_names', methods=['GET'])
def list_unified_names():
    try:
        return jsonify({"status": "success", "users": get_all_unified_enrolled_names()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Query failed: {e}"}), 500


def clear_face_database() -> dict:
    try:
        if os.path.exists(VECTORS_FILE):
            os.remove(VECTORS_FILE)
        if os.path.exists(DATABASE_ROOT):
            shutil.rmtree(DATABASE_ROOT)
        clear_vectors_cache()
        return {"status": "success", "message": "Face database cleared."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@face_bp.route('/delete', methods=['POST'])
def delete_face():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"status": "error", "message": "Missing name"}), 400
    vectors = load_saved_vectors()
    if name not in vectors:
        return jsonify({"status": "error", "message": f"Student '{name}' not found in face database"}), 404
    del vectors[name]
    with open(VECTORS_FILE, "wb") as f:
        pickle.dump(vectors, f)
    clear_vectors_cache()
    person_dir = os.path.join(DATABASE_ROOT, name)
    if os.path.exists(person_dir):
        shutil.rmtree(person_dir)
    return jsonify({"status": "success", "message": f"Face enrollment deleted for {name}"}), 200


@face_bp.route('/photo/<name>', methods=['GET'])
def get_photo(name):
    """获取学生最新的人脸照片"""
    person_dir = os.path.join(DATABASE_ROOT, name.strip())
    if not os.path.isdir(person_dir):
        return jsonify({"status": "error", "message": "Student not found"}), 404
    photos = sorted(glob.glob(os.path.join(person_dir, "*.jpg")), key=os.path.getmtime, reverse=True)
    if not photos:
        return jsonify({"status": "error", "message": "No photo found"}), 404
    return send_file(photos[0], mimetype='image/jpeg')


@face_bp.route('/delete-student', methods=['POST'])
def delete_student():
    """删除学生全部档案（人脸 + 声纹）"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"status": "error", "message": "Missing name"}), 400

    face_deleted = False
    voice_deleted = False

    # 删除人脸
    vectors = load_saved_vectors()
    if name in vectors:
        del vectors[name]
        with open(VECTORS_FILE, "wb") as f:
            pickle.dump(vectors, f)
        clear_vectors_cache()
        face_deleted = True
    person_dir = os.path.join(DATABASE_ROOT, name)
    if os.path.exists(person_dir):
        shutil.rmtree(person_dir)

    # 删除声纹
    try:
        result = delete_voice_enrollment(name)
        voice_deleted = result.get("status") == "success"
    except Exception:
        voice_deleted = False

    if face_deleted or voice_deleted:
        return jsonify({
            "status": "success",
            "message": f"Student '{name}' deleted (face: {face_deleted}, voice: {voice_deleted})",
            "face_deleted": face_deleted,
            "voice_deleted": voice_deleted,
        }), 200
    return jsonify({"status": "error", "message": f"Student '{name}' not found in any database"}), 404


@face_bp.route('/clear', methods=['POST'])
def clear_db():
    result = clear_face_database()
    return jsonify(result), 200 if result['status'] == 'success' else 500
