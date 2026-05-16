import cv2
import numpy as np
import pickle
import os
import time
import datetime
import argparse

# 导入 YOLOv10
from ultralytics import YOLOv10

# --- 文件和目录配置 ---
YOLO_WEIGHTS_FILE = 'best.pt'
BASE_RESULT_DIR = 'result'

# 全局变量：用于存储特定视频的结果目录路径
VIDEO_RESULT_DIR = None

# 全局变量：用于存储所有结果文件的完整路径
TEMP_FRAME_INFO_FILE = None
FACE_RESULTS_FILE = None
FINAL_OUTPUT_FILE = None

# 采样间隔 (秒)
FRAME_INTERVAL_S = 3

# --- 全局模型 ---
yolo_model = None


def init_result_paths(video_path):
    """根据视频路径初始化所有结果文件和目录。"""
    global VIDEO_RESULT_DIR, TEMP_FRAME_INFO_FILE, FACE_RESULTS_FILE, FINAL_OUTPUT_FILE

    # 1. 提取视频文件名（不含扩展名）
    video_basename = os.path.splitext(os.path.basename(video_path))[0]

    # 2. 设置特定视频的结果目录
    VIDEO_RESULT_DIR = os.path.join(BASE_RESULT_DIR, video_basename)

    # 3. 设置文件路径
    TEMP_FRAME_INFO_FILE = os.path.join(VIDEO_RESULT_DIR, 'sampled_frames_info.pkl')
    FACE_RESULTS_FILE = os.path.join(VIDEO_RESULT_DIR, 'face_results.pkl')
    FINAL_OUTPUT_FILE = os.path.join(VIDEO_RESULT_DIR, 'headless_analysis_results.txt')

    # 4. 创建目录
    os.makedirs(VIDEO_RESULT_DIR, exist_ok=True)

    print(f"--- 结果将存储在目录: {VIDEO_RESULT_DIR} ---")


def init_yolo_model():
    """初始化 YOLOv10 模型。"""
    global yolo_model
    print("--- 正在加载 YOLOv10 模型... ---")
    try:
        yolo_model = YOLOv10(YOLO_WEIGHTS_FILE)
        print("--- YOLOv10 模型加载完成。---")
        return True
    except Exception as e:
        print(f"!!! YOLOv10 模型加载失败：{e}")
        return False


def sample_and_save_frames(video_path):
    """
    1. 采样视频帧（每3秒一帧）。
    2. 将采样帧保存为临时文件。
    3. 返回包含路径和时间戳的列表，并保存到 pickle 文件。
    """
    global VIDEO_RESULT_DIR, TEMP_FRAME_INFO_FILE

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频文件：{video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)

    sampled_frames_info = []
    last_record_time = -FRAME_INTERVAL_S
    frame_count = 0
    start_time_abs = time.time()

    print(f"\n--- 步骤 1: 视频采样开始 (每 {FRAME_INTERVAL_S} 秒一帧) ---")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        current_video_time = frame_count / fps

        # 检查是否到达采样间隔
        if current_video_time - last_record_time >= FRAME_INTERVAL_S:
            # 1. 保存帧图像
            frame_filename = os.path.join(VIDEO_RESULT_DIR, f"frame_{frame_count:06d}.jpg")
            cv2.imwrite(frame_filename, frame)

            # 2. 记录信息
            sampled_frames_info.append({
                "path": frame_filename,
                "time": start_time_abs + current_video_time,
                "frame_count": frame_count,
                "video_time": current_video_time
            })
            last_record_time = current_video_time

            if frame_count % (int(fps * 60)) == 0:
                print(f"  采样进度：已处理 {int(current_video_time)} 秒 / {frame_count} 帧...")

    cap.release()

    # 3. 将采样信息保存到临时文件
    with open(TEMP_FRAME_INFO_FILE, 'wb') as f:
        pickle.dump(sampled_frames_info, f)

    print(f"--- 视频采样完成。共 {len(sampled_frames_info)} 帧。---")
    return sampled_frames_info


def run_face_worker():
    """步骤 2: 在当前进程内运行人脸识别（与 Flask/YOLO 共用同一环境）。"""
    global TEMP_FRAME_INFO_FILE, FACE_RESULTS_FILE

    print("\n--- 步骤 2: 启动人脸识别 (同进程) ---")

    try:
        from face_worker import process_and_save
        process_and_save(TEMP_FRAME_INFO_FILE, FACE_RESULTS_FILE)
        print("--- 人脸识别执行成功。---")

        if os.path.exists(TEMP_FRAME_INFO_FILE):
            os.remove(TEMP_FRAME_INFO_FILE)

    except Exception as e:
        print(f"!!! 人脸识别失败：{e}")
        raise RuntimeError("人脸识别失败，请检查 InsightFace / onnxruntime 配置。") from e


def run_yolo_detection_and_merge(sampled_frames_info):
    """
    步骤 3: 运行 YOLO 检测，加载人脸结果，然后合并并输出最终报告。
    """
    global FACE_RESULTS_FILE

    if not init_yolo_model():
        return

    if not os.path.exists(FACE_RESULTS_FILE):
        raise FileNotFoundError(f"找不到人脸识别结果文件：{FACE_RESULTS_FILE}，请检查步骤2是否成功。")

    # 1. 加载人脸识别结果
    with open(FACE_RESULTS_FILE, 'rb') as f:
        face_results_list = pickle.load(f)

    # 将人脸结果转换为字典
    face_data_map = {res['frame_path']: res for res in face_results_list}

    final_video_results = []
    print("\n--- 步骤 3: YOLO 检测和数据合并开始 ---")

    for i, frame_info in enumerate(sampled_frames_info):
        frame_path = frame_info['path']
        frame_time = frame_info['time']

        # 从人脸结果中获取人脸信息
        face_res = face_data_map.get(frame_path, {})
        face_data = face_res.get('face_data', [])

        # 运行 YOLOv10 检测
        try:
            frame_bgr = cv2.imread(frame_path)
            if frame_bgr is None:
                print(f"!!! 警告：无法加载帧 {frame_path} 进行 YOLO 检测，跳过。")
                continue

            yolo_results = yolo_model.predict(frame_bgr, verbose=False)[0]

            yolo_boxes = []
            for box in yolo_results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls = int(box.cls[0].item())
                object_name = yolo_model.names[cls]
                yolo_boxes.append({"name": object_name, "bbox": [x1, y1, x2, y2]})

        except Exception as e:
            print(f"!!! YOLO 检测失败：{e}，跳过此帧。")
            yolo_boxes = []

        # --- 关联人脸和行为 ---
        current_actions = []

        if not face_data:
            final_video_results.append({
                "time": frame_time,
                "actions": [],
            })
            continue

        for face_item in face_data:
            person_name = face_item['name']
            face_bbox = np.array(face_item['bbox'])
            associated_objects = set()

            # 遍历 YOLO 检测到的所有物体，检查是否与人脸框重叠 (IoU > 0)
            for yolo_item in yolo_boxes:
                object_name = yolo_item['name']
                [x1, y1, x2, y2] = yolo_item['bbox']

                # 关联逻辑: 检查边界框重叠
                inter_x1 = max(face_bbox[0], x1)
                inter_y1 = max(face_bbox[1], y1)
                inter_x2 = min(face_bbox[2], x2)
                inter_y2 = min(face_bbox[3], y2)

                if max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1) > 0:
                    associated_objects.add(object_name)

            # 4. 生成结果文本
            if associated_objects:
                actions_list = ', '.join(associated_objects)
                action_string = f"{person_name}: {actions_list}"
                current_actions.append(action_string)
            else:
                current_actions.append(f"{person_name}: 无关联行为")

        # 记录最终结果
        final_video_results.append({
            "time": frame_time,
            "actions": current_actions
        })

        if (i + 1) % 50 == 0:
            print(f"  合并进度：已处理 {i + 1} 帧... ---")

    print("--- YOLO 检测和数据合并完成。---")

    # 2. 输出最终报告
    output_results(final_video_results)


def output_results(video_results):
    """将关联结果写入文件，格式与原要求一致。"""
    global FINAL_OUTPUT_FILE

    if not video_results:
        print("没有检测到任何结果，未生成文件。")
        return

    with open(FINAL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("### 视频人脸与行为关联分析结果 (Headless 模式) ###\n")
        f.write(f"采样间隔: {FRAME_INTERVAL_S} 秒\n\n")

        for res in video_results:
            # 假设 res['time'] 存储的是绝对时间戳
            readable_time = datetime.datetime.fromtimestamp(res['time']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            f.write(f"时间：{readable_time}\n")
            if res['actions']:
                actions_str = '\n    - '.join(res['actions'])
                f.write(f"  关联结果：\n    - {actions_str}\n\n")
            else:
                f.write(f"  关联结果：未检测到人物或关联行为。\n\n")

    print(f"✅ 分析完成！结果已保存到文件：{FINAL_OUTPUT_FILE}")


def main(video_path):
    """主函数：处理整个视频文件。"""

    # 根据视频路径初始化结果目录和文件路径
    init_result_paths(video_path)

    # 步骤 1: 采样视频并保存帧
    sampled_frames_info = sample_and_save_frames(video_path)
    if not sampled_frames_info:
        print("!!! 错误：视频中未采样到任何帧。")
        return

    try:
        run_face_worker()

        # 步骤 3: 运行 YOLO 检测和数据合并
        run_yolo_detection_and_merge(sampled_frames_info)

        # 清理人脸结果文件
        if os.path.exists(FACE_RESULTS_FILE):
            os.remove(FACE_RESULTS_FILE)

    except Exception as e:
        print(f"!!! 致命错误：{e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="主控制脚本：Headless 模式视频人脸与行为关联分析工具 (YOLO 环境)。")
    parser.add_argument("video_path", type=str, help="要分析的视频文件的完整路径。")
    args = parser.parse_args()

    # 确保依赖文件存在性检查
    if not os.path.exists(args.video_path):
        print(f"!!! 错误：找不到文件：{args.video_path}")
    elif not os.path.exists(YOLO_WEIGHTS_FILE):
        print(f"!!! 错误：找不到 YOLO 模型权重文件：{YOLO_WEIGHTS_FILE}")
    else:
        # 确保 face_worker.py 存在
        if not os.path.exists('face_worker.py'):
            print("!!! 错误：找不到 'face_worker.py' 脚本，请将其放在根目录下。")
        else:
            main(args.video_path)