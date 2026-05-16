#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""声纹识别与语音转录 API"""
import os
import traceback
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from dotenv import load_dotenv

from api.voice_core_api import enroll_voice_data, get_voice_system, get_voice_config

load_dotenv()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'mp4', 'mov', 'avi', 'webm'}
AUDIO_EXTENSIONS = {'webm', 'wav', 'mp3', 'm4a'}

voice_bp = Blueprint('voice_api', __name__, url_prefix='/api/voice')
config = get_voice_config()


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _file_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lstrip('.').lower()


def _standardize_audio(src_path: str, filename: str) -> tuple[str, str | None]:
    """转码为 16kHz 单声道 WAV；返回 (处理路径, 临时文件路径或 None)。"""
    ext = _file_ext(filename)
    if ext not in AUDIO_EXTENSIONS:
        return src_path, None

    base = os.path.splitext(filename)[0]
    wav_path = os.path.join(UPLOAD_FOLDER, f"{base}_standardized.wav")
    audio = AudioSegment.from_file(src_path, format=ext)
    audio.export(wav_path, format="wav", parameters=["-ac", "1", "-ar", "16000"])
    return wav_path, wav_path


@voice_bp.route('/enroll', methods=['POST'])
def enroll_voice():
    if 'voice_file' not in request.files or 'name' not in request.form:
        return jsonify({"status": "error", "message": "缺少文件或姓名参数"}), 400

    file = request.files['voice_file']
    name = request.form['name']
    if file.filename == '' or not _allowed_file(file.filename):
        return jsonify({"status": "error", "message": "未选择文件或文件类型不允许"}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(temp_path)
    temp_wav_path = None

    try:
        core_path, temp_wav_path = _standardize_audio(temp_path, filename)
        result = enroll_voice_data(name, core_path)
        if result['status'] == 'success':
            return jsonify({"status": "success", "message": f"声纹 {name} 录入成功!"}), 200
        return jsonify({"status": "error", "message": result.get('message', '声纹录入失败')}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"声纹处理失败：{str(e)}"}), 500
    finally:
        for p in (temp_path, temp_wav_path):
            if p and os.path.exists(p):
                os.remove(p)


@voice_bp.route('/transcribe', methods=['POST'])
def transcribe_audio_or_video():
    if 'file' not in request.files:
        return jsonify({"error": "缺少文件部分"}), 400

    file = request.files['file']
    if file.filename == '' or not _allowed_file(file.filename):
        return jsonify({"error": "未选择文件或文件类型不允许"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    transcript_path = os.path.join(config.OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_transcript.txt")

    try:
        file.save(filepath)
        get_voice_system().process_video(filepath, output_file=transcript_path, use_voiceprint=True)
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return jsonify({"transcript": f.read()}), 200
        return jsonify({"error": "生成转录文件失败"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"转录过程中发生错误: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
