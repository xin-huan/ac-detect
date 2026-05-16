# ac-detect 环境说明

## 推荐：单一环境 `ac_detect`

本项目原先拆分为 `env_face`（InsightFace + numpy 2.x）与 `env_yolo`（YOLO + 语音），
与主 Flask 环境 `env_ac`（numpy 1.26 + CPU PyTorch）存在 **numpy / PyTorch 版本冲突**。

现已统一为 **`ac_detect`**，所有模块在同一进程中运行：

| 模块 | 技术栈 | 版本要点 |
|------|--------|----------|
| 人脸录入/识别 | InsightFace `buffalo_l` | insightface 0.7.3, onnxruntime |
| 行为检测 | YOLOv10 (`best.pt`) | ultralytics 8.3.x, torch 2.0.1 |
| 声纹/转写 | Whisper + pyannote | whisper, pyannote.audio 3.1.x |
| Web 服务 | Flask | flask 3.x |

**关键约束（不可随意升级）：**

- `numpy==1.26.4` — onnxruntime / pyannote 与 numpy 2.x 不兼容
- `torch==2.0.1` — 与 ultralytics、pyannote、insightface 均已验证
- `python==3.10`

## 安装

```powershell
cd C:\Users\80943\model\ac-detect
powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
conda activate ac_detect
```

或手动：

```bash
conda env create -f envs/ac_detect.yml
```

## 环境变量

在项目根目录 `.env`：

```
HF_TOKEN=hf_xxxxxxxx
```

在 [HuggingFace](https://huggingface.co/settings/tokens) 创建 Token，并接受以下模型协议：

- `pyannote/speaker-diarization-3.1`
- `pyannote/embedding`
- `pyannote/voice-activity-detection`

## 运行

```bash
conda activate ac_detect
python app.py          # Web 服务 http://0.0.0.0:5000
python yolo_main_analysis.py testvideo/xxx.mp4   # 命令行分析
```

