import os
import sys
import pickle
import cv2

os.environ.setdefault("PYTHONUTF8", "1")

from face_common import get_face_app, load_saved_vectors, match_face


def process_and_save(frame_paths_file: str, output_file: str) -> None:
    """对采样帧做人脸识别，结果写入 pickle。"""
    load_saved_vectors()
    face_app = get_face_app()

    with open(frame_paths_file, 'rb') as f:
        sampled_frames_info = pickle.load(f)

    face_results = []
    print(f"--- [Face Worker] 发现 {len(sampled_frames_info)} 帧需要处理。---")

    for i, info in enumerate(sampled_frames_info):
        frame_path = info['path']
        frame_bgr = cv2.imread(frame_path)
        if frame_bgr is None:
            print(f"!!! [Face Worker] 无法读取帧文件：{frame_path}")
            continue

        current_face_data = []
        for face in face_app.get(frame_bgr) or []:
            current_face_data.append({
                "name": match_face(face.embedding),
                "bbox": face.bbox.astype(int).tolist(),
            })

        face_results.append({
            "frame_path": frame_path,
            "time": info['time'],
            "face_data": current_face_data,
        })

        if (i + 1) % 50 == 0:
            print(f"--- [Face Worker] 已处理 {i + 1} 帧... ---")

    with open(output_file, 'wb') as f:
        pickle.dump(face_results, f)

    print(f"--- [Face Worker] 人脸识别完成。结果已保存到 {output_file} ---")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python face_worker.py <帧路径列表文件> <输出文件路径>")
        sys.exit(1)
    process_and_save(sys.argv[1], sys.argv[2])
