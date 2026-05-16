from collections import defaultdict
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import traceback
from pathlib import Path

import yolo_main_analysis
import compute_attention_score as cas
from api.voice_core_api import get_voice_system, get_voice_config

integrated_bp = Blueprint('integrated_analysis', __name__, url_prefix='/api/analysis')

UPLOAD_FOLDER = 'temp_analysis_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _per_person_score_map(per_person_list) -> dict:
    if isinstance(per_person_list, dict):
        return per_person_list
    return {row["name"]: row["avg_score"] for row in (per_person_list or [])}


def _build_per_student_speech(voice_results: list) -> dict:
    """将声纹匹配后的语音结果按学生姓名聚合"""
    per_student = defaultdict(list)
    for seg in (voice_results or []):
        name = seg.get("speaker", "未知学生")
        text = seg.get("text", "").strip()
        if text:
            per_student[name].append(text)
    return {name: " ".join(texts) for name, texts in per_student.items()}


def _get_all_enrolled_names_safe() -> list:
    """安全获取所有已建档学生姓名（声纹模块可能未就绪）"""
    try:
        from api.face_api import get_all_unified_enrolled_names
        return [u["name"] for u in get_all_unified_enrolled_names()]
    except Exception:
        pass
    # 回退：仅从人脸库获取
    try:
        from face_common import load_saved_vectors
        return list(load_saved_vectors().keys())
    except Exception:
        return []


@integrated_bp.route('/analyze', methods=['POST'])
def analyze_video_integrated():
    if 'video_file' not in request.files:
        return jsonify({"status": "error", "message": "Missing video file"}), 400

    video_file = request.files['video_file']
    filename = secure_filename(video_file.filename)
    temp_video_path = os.path.join(UPLOAD_FOLDER, filename)
    video_file.save(temp_video_path)
    transcript_path = None

    try:
        # YOLO 行为检测（先跑，不依赖声纹模块）
        yolo_main_analysis.main(temp_video_path)
        log_path = yolo_main_analysis.FINAL_OUTPUT_FILE

        if not log_path or not os.path.exists(log_path):
            raise FileNotFoundError("YOLO analysis log missing.")

        blocks = cas.parse_log_file(log_path)

        # 行为评分
        if blocks:
            overall_score, _, per_person_list = cas.compute_scores(blocks)
            per_person_scores = _per_person_score_map(per_person_list)
            person_events = cas.get_person_timeline_events(blocks)

            present_students = list(per_person_scores.keys())
            if not present_students:
                for block in blocks:
                    for name, _ in block.get("pairs", []):
                        if name not in present_students:
                            present_students.append(name)
        else:
            overall_score = 0.0
            per_person_scores = {}
            person_events = {}
            present_students = []

        # 语音识别 + 声纹匹配（非致命：失败时用空结果继续）
        voice_results = []
        transcript_content = "未识别到语音内容。"
        per_student_speech = {}
        try:
            basename = os.path.splitext(filename)[0]
            voice_config = get_voice_config()
            transcript_path = Path(voice_config.OUTPUT_DIR) / f"{basename}_transcript.txt"

            voice_results = get_voice_system().process_video(
                temp_video_path, output_file=str(transcript_path), use_voiceprint=True
            )

            if transcript_path.exists():
                transcript_content = transcript_path.read_text(encoding='utf-8')

            per_student_speech = _build_per_student_speech(voice_results)
        except Exception as voice_err:
            print(f"[WARNING] 语音处理失败，跳过: {voice_err}")

        # 考勤：以所有已建档学生为全集
        all_enrolled_names = _get_all_enrolled_names_safe()
        total_enrolled = len(all_enrolled_names)

        # 合并 YOLO 检测到的学生 + 声纹识别到的学生
        voice_detected = list(per_student_speech.keys())
        all_detected_names = set(present_students) | set(voice_detected)

        # 过滤掉"未知人物"，只保留已建档学生
        actual_present = [n for n in all_enrolled_names if n in all_detected_names]

        # 生成全体已建档学生的报告
        if all_enrolled_names:
            students_report = []
            for name in all_enrolled_names:
                score = per_person_scores.get(name, 0.0)
                students_report.append({
                    "name": name,
                    "concentration_score": round(score * 100),
                    "behavior_events": person_events.get(name, []),
                    "speech_content": per_student_speech.get(name, "该学生在视频中未检测到发言。"),
                })
            students_report.sort(key=lambda s: s["concentration_score"], reverse=True)
        else:
            # 无已建档学生时，回退到仅展示检测到的学生
            students_report = [{
                "name": name,
                "concentration_score": round(per_person_scores.get(name, 0.0) * 100),
                "behavior_events": person_events.get(name, []),
                "speech_content": per_student_speech.get(name, transcript_content),
            } for name in all_detected_names if name != "未知人物"]
            students_report.sort(key=lambda s: s["concentration_score"], reverse=True)
            total_enrolled = len(students_report)

        return jsonify({
            "status": "success",
            "message": "Integrated analysis successful.",
            "result": {
                "summary": {
                    "attendance": {"present": actual_present, "total": total_enrolled},
                    "average_score": round(overall_score * 100),
                    "full_transcript": transcript_content,
                },
                "students": students_report,
            },
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Backend processing failed.", "error": str(e)}), 500

    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if transcript_path and transcript_path.exists():
            transcript_path.unlink()
