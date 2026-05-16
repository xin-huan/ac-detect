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
        yolo_main_analysis.main(temp_video_path)
        log_path = yolo_main_analysis.FINAL_OUTPUT_FILE

        if not log_path or not os.path.exists(log_path):
            raise FileNotFoundError("YOLO analysis log missing.")

        blocks = cas.parse_log_file(log_path)
        if not blocks:
            return jsonify({
                "status": "success",
                "message": "No behavior detected.",
                "result": {
                    "summary": {"attendance": {"present": [], "total": 0}, "average_score": 0, "full_transcript": ""},
                    "students": [],
                },
            })

        overall_score, _, per_person_list = cas.compute_scores(blocks)
        per_person_scores = _per_person_score_map(per_person_list)
        person_events = cas.get_person_timeline_events(blocks)

        present_students = list(per_person_scores.keys())
        if not present_students:
            for block in blocks:
                for name, _ in block.get("pairs", []):
                    if name not in present_students:
                        present_students.append(name)

        basename = os.path.splitext(filename)[0]
        voice_config = get_voice_config()
        transcript_path = Path(voice_config.OUTPUT_DIR) / f"{basename}_transcript.txt"

        get_voice_system().process_video(
            temp_video_path, output_file=str(transcript_path), use_voiceprint=True
        )

        transcript_content = "未识别到语音内容。"
        if transcript_path.exists():
            transcript_content = transcript_path.read_text(encoding='utf-8')

        students_report = [{
            "name": name,
            "concentration_score": round(per_person_scores.get(name, 0.0) * 100),
            "behavior_events": person_events.get(name, []),
            "speech_content": transcript_content,
        } for name in present_students]

        return jsonify({
            "status": "success",
            "message": "Integrated analysis successful.",
            "result": {
                "summary": {
                    "attendance": {"present": present_students, "total": len(present_students)},
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
