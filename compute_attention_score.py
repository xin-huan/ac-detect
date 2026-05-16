import argparse
import csv
import json
import os
import re
from collections import defaultdict

# 专注度计算权重模型
BEHAVIOR_WEIGHTS = {
    "play_phone": 0.10,
    "sleep": 0.00,
    "stand": 0.70,
    "hand_up": 0.90,
    "write": 0.80,
    "drink": 0.40,
    "无关联行为": 0.30,
}

DEFAULT_UNKNOWN_BEHAVIOR_SCORE = 0.40

# 日志解析正则表达式
TIME_PATTERNS = (r"^时间[:：]\s*(.+?)\s*$", r"^Time[:：]\s*(.+?)\s*$")
PAIR_PATTERN = re.compile(r"^\s*-\s*(.+?)\s*:\s*(.+?)\s*$")


def parse_log_file(path):
    """解析时序多模态日志文件至结构化数据块"""
    blocks = []
    cur = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue

            matched_time = None
            for p in TIME_PATTERNS:
                m = re.match(p, s)
                if m:
                    matched_time = m.group(1)
                    break

            if matched_time:
                if cur:
                    blocks.append(cur)
                cur = {"timestamp": matched_time, "pairs": []}
                continue

            m = PAIR_PATTERN.match(s)
            if m:
                name = m.group(1).strip()
                behavior = m.group(2).strip()
                if cur is None:
                    cur = {"timestamp": "UNKNOWN_TIME", "pairs": []}
                cur["pairs"].append((name, behavior))

        if cur:
            blocks.append(cur)
    return blocks


def score_of_behavior(behavior):
    """基于行为字典映射专注度权重分值"""
    global BEHAVIOR_WEIGHTS, DEFAULT_UNKNOWN_BEHAVIOR_SCORE
    return BEHAVIOR_WEIGHTS.get(behavior, DEFAULT_UNKNOWN_BEHAVIOR_SCORE)


def compute_scores(blocks):
    """核心算法：计算群体时序趋势与个体均值专注度"""
    timeline = []
    per_person_sum = defaultdict(float)
    per_person_cnt = defaultdict(int)

    total_people = 0
    weighted_sum = 0.0

    for blk in blocks:
        ts = blk["timestamp"]
        pairs = blk["pairs"]

        frame_scores = []
        seen_person_in_frame = set()

        for name, behavior in pairs:
            sc = score_of_behavior(behavior)
            frame_scores.append(sc)

            key = name
            if key not in seen_person_in_frame:
                per_person_sum[key] += sc
                per_person_cnt[key] += 1
                seen_person_in_frame.add(key)

        if frame_scores:
            avg = sum(frame_scores) / len(frame_scores)
            n = len(frame_scores)
            timeline.append({"timestamp": ts, "score": avg, "num_people": n})
            weighted_sum += avg * n
            total_people += n
        else:
            timeline.append({"timestamp": ts, "score": None, "num_people": 0})

    overall = (weighted_sum / total_people) if total_people > 0 else 0.0

    per_person = []
    for name in per_person_sum:
        cnt = per_person_cnt[name]
        avg = per_person_sum[name] / max(cnt, 1)
        per_person.append({"name": name, "avg_score": avg, "frames": cnt})
    per_person.sort(key=lambda x: x["avg_score"], reverse=True)

    return overall, timeline, per_person


def get_person_timeline_events(blocks):
    """提取个体维度下的时序行为事件序列"""
    person_events = defaultdict(list)

    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        ts = blk.get('timestamp') or blk.get('time')
        if not ts:
            continue

        if 'pairs' in blk and isinstance(blk['pairs'], list):
            for name, behavior in blk['pairs']:
                person_events[name].append({
                    "time": ts,
                    "name": behavior,
                    "detail": f"Weight: {score_of_behavior(behavior):.2f}"
                })

    return dict(person_events)


def save_outputs(out_json_path, behavior_weights, overall, timeline, per_person, person_csv_path,
                 person_timeline_csv_path, blocks):
    """将计算结果持久化为 JSON 与多维 CSV 报表"""
    out_dir = os.path.dirname(out_json_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    data = {
        "behavior_weights": behavior_weights,
        "overall_score": overall,
        "overall_score_percent": round(overall * 100, 2),
        "timeline": timeline,
        "per_person": per_person,
    }
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(person_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "avg_score", "frames"])
        for row in per_person:
            w.writerow([row["name"], f"{row['avg_score']:.4f}", row["frames"]])

    with open(person_timeline_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "name", "behavior", "behavior_score"])
        for blk in blocks:
            ts = blk["timestamp"]
            for name, behavior in blk["pairs"]:
                w.writerow([ts, name, behavior, f"{score_of_behavior(behavior):.4f}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log_path", help="Path to input headless_analysis_results.txt")
    ap.add_argument("--out", default="attention_summary.json", help="Path to output JSON")
    args = ap.parse_args()

    blocks = parse_log_file(args.log_path)
    overall, timeline, per_person = compute_scores(blocks)

    out_json = args.out
    out_dir = os.path.dirname(out_json) or "."
    person_csv = os.path.join(out_dir, "attention_per_person_summary.csv")
    person_timeline_csv = os.path.join(out_dir, "attention_per_person_timeline.csv")

    save_outputs(
        out_json,
        BEHAVIOR_WEIGHTS,
        overall,
        timeline,
        per_person,
        person_csv,
        person_timeline_csv,
        blocks,
    )


if __name__ == "__main__":
    main()