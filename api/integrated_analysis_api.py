from collections import defaultdict
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
import time
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


REPORTS_INDEX_FILE = os.path.join('result', '_reports_index.json')


def _load_history_index() -> list:
    """加载历史报告索引"""
    if os.path.exists(REPORTS_INDEX_FILE):
        try:
            with open(REPORTS_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_history_index(index: list) -> None:
    """保存历史报告索引"""
    os.makedirs('result', exist_ok=True)
    with open(REPORTS_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _save_report(video_name: str, result: dict) -> None:
    """将分析报告持久化到磁盘"""
    report_dir = os.path.join('result', video_name)
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, 'analysis_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 更新索引
    index = _load_history_index()
    # 移除同一视频名的旧记录
    index = [entry for entry in index if entry.get('video_name') != video_name]
    index.insert(0, {
        'video_name': video_name,
        'timestamp': time.time(),
        'average_score': result.get('summary', {}).get('average_score', 0),
        'student_count': len(result.get('students', [])),
        'attendance_total': result.get('summary', {}).get('attendance', {}).get('total', 0),
        'attendance_present': len(result.get('summary', {}).get('attendance', {}).get('present', [])),
    })
    _save_history_index(index)


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

        result = {
            "summary": {
                "attendance": {"present": actual_present, "total": total_enrolled},
                "average_score": round(overall_score * 100),
                "full_transcript": transcript_content,
            },
            "students": students_report,
        }

        # 持久化保存报告
        try:
            video_basename = os.path.splitext(filename)[0]
            _save_report(video_basename, result)
        except Exception as save_err:
            print(f"[WARNING] 报告持久化失败: {save_err}")

        return jsonify({
            "status": "success",
            "message": "Integrated analysis successful.",
            "result": result,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Backend processing failed.", "error": str(e)}), 500

    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if transcript_path and transcript_path.exists():
            transcript_path.unlink()


@integrated_bp.route('/history', methods=['GET'])
def list_history():
    """列出所有历史分析报告"""
    try:
        index = _load_history_index()
        return jsonify({"status": "success", "reports": index}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@integrated_bp.route('/report/<video_name>', methods=['GET'])
def get_report(video_name):
    """获取指定视频的历史分析报告"""
    try:
        report_path = os.path.join('result', video_name, 'analysis_report.json')
        if not os.path.exists(report_path):
            return jsonify({"status": "error", "message": "Report not found"}), 404
        with open(report_path, 'r', encoding='utf-8') as f:
            return jsonify({"status": "success", "result": json.load(f)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@integrated_bp.route('/report/<video_name>', methods=['DELETE'])
def delete_report(video_name):
    """删除历史分析报告"""
    try:
        import shutil
        report_dir = os.path.join('result', video_name)
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
        index = _load_history_index()
        index = [e for e in index if e.get('video_name') != video_name]
        _save_history_index(index)
        return jsonify({"status": "success", "message": f"Report '{video_name}' deleted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
