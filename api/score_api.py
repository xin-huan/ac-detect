from __future__ import annotations
import os
import json
import uuid
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify

try:
    import compute_attention_score as cas
except Exception as e:
    cas = None
    _import_err = e

score_bp = Blueprint("score_api", __name__, url_prefix="/api/score")

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _safe_float_dict(d: Dict[str, Any]) -> Dict[str, float]:
    """类型安全的浮点数字典转换映射"""
    out = {}
    for k, v in (d or {}).items():
        try:
            out[str(k)] = float(v)
        except Exception:
            continue
    return out

def _current_defaults() -> Dict[str, Any]:
    """加载系统预设的专注度行为权重与基准分值"""
    defaults = {"weights": {}, "unknown_score": 0.0}
    if not cas:
        return defaults

    if hasattr(cas, "BEHAVIOR_WEIGHTS") and isinstance(cas.BEHAVIOR_WEIGHTS, dict):
        defaults["weights"] = {str(k): float(v) for k, v in cas.BEHAVIOR_WEIGHTS.items()}

    if hasattr(cas, "DEFAULT_UNKNOWN_BEHAVIOR_SCORE"):
        try:
            defaults["unknown_score"] = float(cas.DEFAULT_UNKNOWN_BEHAVIOR_SCORE)
        except Exception:
            pass
    return defaults

def _run_scoring(log_path: Path, out_dir: Path, weights: Optional[Dict[str, float]] = None, unknown_score: Optional[float] = None) -> Dict[str, Any]:
    """调度评分核心算法，支持动态权重注入与多维结果序列化"""
    if cas is None:
        raise RuntimeError(f"Score module import failed: {_import_err}")
    if not hasattr(cas, "parse_log_file") or not hasattr(cas, "compute_scores"):
        raise RuntimeError("Missing core functions in compute_attention_score.")

    _ensure_dir(out_dir)
    out_json = out_dir / "attention_summary.json"
    person_csv = out_dir / "attention_per_person_summary.csv"
    person_timeline_csv = out_dir / "attention_per_person_timeline.csv"

    restore_weights = None
    restore_unknown = None

    if weights is not None and hasattr(cas, "BEHAVIOR_WEIGHTS"):
        restore_weights = dict(getattr(cas, "BEHAVIOR_WEIGHTS", {}))
        cas.BEHAVIOR_WEIGHTS = dict(weights)

    if unknown_score is not None and hasattr(cas, "DEFAULT_UNKNOWN_BEHAVIOR_SCORE"):
        try:
            restore_unknown = float(getattr(cas, "DEFAULT_UNKNOWN_BEHAVIOR_SCORE"))
            cas.DEFAULT_UNKNOWN_BEHAVIOR_SCORE = float(unknown_score)
        except Exception:
            pass

    try:
        blocks = cas.parse_log_file(str(log_path))
        overall, timeline, per_person = cas.compute_scores(blocks)

        if hasattr(cas, "save_outputs"):
            cas.save_outputs(
                str(out_json), getattr(cas, "BEHAVIOR_WEIGHTS", {}),
                overall, timeline, per_person, str(person_csv), str(person_timeline_csv), blocks
            )
        else:
            data = {
                "behavior_weights": getattr(cas, "BEHAVIOR_WEIGHTS", {}),
                "overall_score": overall,
                "overall_score_percent": round(overall * 100, 2),
                "timeline": timeline,
                "per_person": per_person,
            }
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "status": "success", "overall": overall,
            "timeline_len": len(timeline), "per_person_len": len(per_person),
            "paths": {
                "summary_json": str(out_json), "per_person_csv": str(person_csv),
                "person_timeline_csv": str(person_timeline_csv),
            },
        }
    finally:
        if restore_weights is not None:
            cas.BEHAVIOR_WEIGHTS = restore_weights
        if restore_unknown is not None:
            cas.DEFAULT_UNKNOWN_BEHAVIOR_SCORE = restore_unknown

@score_bp.route("/defaults", methods=["GET"])
def get_defaults():
    try:
        return jsonify({"status": "success", **_current_defaults()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@score_bp.route("/compute", methods=["POST"])
def compute_from_path():
    """基于持久化多模态分析日志的专注度计算接口"""
    try:
        if not cas:
            return jsonify({"status": "error", "message": f"Module error: {_import_err}"}), 500

        data = request.get_json(silent=True) or {}
        log_path = Path(str(data.get("log_path", "")).strip())
        if not log_path.exists():
            return jsonify({"status": "error", "message": f"File not found: {log_path}"}), 404

        out_dir = Path(str(data.get("out_dir") or log_path.parent))
        weights = _safe_float_dict(data.get("weights") or {})
        unknown = data.get("unknown_score", None)
        
        if unknown is not None:
            try:
                unknown = float(unknown)
            except Exception:
                return jsonify({"status": "error", "message": "unknown_score must be numeric"}), 400

        result = _run_scoring(log_path, out_dir, weights or None, unknown)
        return jsonify(result), 200
    except Exception:
        return jsonify({"status": "error", "message": "Computation failed", "trace": traceback.format_exc()}), 500

@score_bp.route("/compute-upload", methods=["POST"])
def compute_from_upload():
    """处理文件流式上传的专注度联合计算接口"""
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "Missing file"}), 400

        f = request.files["file"]
        if not f.filename:
            return jsonify({"status": "error", "message": "Empty filename"}), 400

        out_dir = Path("result") / "_uploads" / uuid.uuid4().hex
        _ensure_dir(out_dir)
        log_path = out_dir / "headless_analysis_results.txt"
        f.save(str(log_path))

        weights_raw = request.form.get("weights")
        weights = None
        if weights_raw:
            try:
                weights = _safe_float_dict(json.loads(weights_raw))
            except Exception:
                return jsonify({"status": "error", "message": "weights must be JSON"}), 400

        unknown = request.form.get("unknown_score")
        if unknown is not None:
            try:
                unknown = float(unknown)
            except Exception:
                return jsonify({"status": "error", "message": "unknown_score must be numeric"}), 400

        result = _run_scoring(log_path, out_dir, weights, unknown)
        return jsonify(result), 200
    except Exception:
        return jsonify({"status": "error", "message": "Computation failed", "trace": traceback.format_exc()}), 500

@score_bp.route("/preview", methods=["GET"])
def preview_json():
    """提供专注度分析快照数据的只读视图接口"""
    try:
        path_str = request.args.get("path", "").strip()
        if not path_str:
            return jsonify({"status": "error", "message": "Missing path parameter"}), 400

        p = Path(path_str)
        if not p.exists():
            return jsonify({"status": "error", "message": f"File not found: {p}"}), 404

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"status": "success", "data": data}), 200
    except Exception:
        return jsonify({"status": "error", "message": "Read failed", "trace": traceback.format_exc()}), 500