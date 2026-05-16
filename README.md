## 🛠️ 环境准备

本项目使用 **单一 Conda 环境 `ac_detect`**，同时运行人脸、YOLO 行为检测与语音模块。

### 1. 创建环境

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
```

或：

```bash
conda env create -f envs/ac_detect.yml
```

### 2. 配置 HuggingFace Token

在项目根目录创建 `.env`：

```
HF_TOKEN=你的HuggingFace令牌
```

### 3. 激活环境

```bash
conda activate ac_detect
```

## 💻 系统运行

### Web 服务

```bash
python app.py
```

浏览器访问 `http://localhost:5000`

### 命令行视频分析

```bash
python yolo_main_analysis.py testvideo/你的视频.mp4
```

### 结果查看

程序运行完成后，所有检测和分析结果将保存在项目根目录下的 result 文件夹内。

## 开发规范！！！

为便于维护和开发，现定下开发规范：

1. **测试视频存放位置**  
   - 测试视频应位于且**唯一位于**新创建的 `testvideo` 文件夹下。  
   - 需修改代码，确保能够正确读取该文件夹下的指定视频。  
   - 这样便于前端上传视频的逻辑，上传后即可直接放在该目录下进行后续识别工作。

2. **结果文件存放位置**  
   - 所有最终生成的唯一结果文件应位于 `result` 文件夹下。  
   - 示例：`result/1` 文件夹下应包含 `headless_analysis_results.txt`。  
   - 语音识别结果和评分计算结果也应放在该文件夹内。  
   - 这样界面和结果读取逻辑都可以统一从此目录获取，无需到处查找。

3. **中间文件存放规范**  
   - 除最终结果的 `.txt` 文件外，  
     所有过程生成的中间文件都应保存在**各自系统内部的文件夹**中，  
     不得散落在项目根目录或结果目录下。


## 🧱 项目结构示例 (Project Structure Example)

```
ac-detect/
├── api/                          # 后端 API 接口
│   ├── __init__.py
│   ├── face_api.py               # 人脸识别相关接口
│   ├── voice_api.py              # 声纹识别相关接口
│   ├── voice_core_api.py         # 声纹核心接口
│   ├── integrated_analysis_api.py # 综合分析接口
│   └── score_api.py              # 评分接口
├── app.py                        # Flask Web 主程序入口
├── face_common.py                # 人脸识别通用函数
├── face_worker.py                # 人脸识别后台工作线程
├── yolo_main_analysis.py         # 命令行视频分析入口
├── compute_attention_score.py    # 注意力评分计算
├── best.pt                       # YOLO 行为检测模型权重
├── voice_database.pkl            # 声纹特征数据库
├── insightface-master/           # 人脸识别模块（特征提取、数据库管理）
│   ├── face_database/            # 已注册人脸库
│   │   ├── 234/
│   │   ├── Papi/
│   │   └── 罗翔/
│   └── face_vectors.pkl          # 人脸特征向量
├── ultralytics/                  # YOLO 行为识别模块（目标检测）
├── voice_system/                 # 声纹识别模块（特征提取、声纹库管理）
│   ├── voice_recognition_system.py
│   ├── audio_extractor.py        # 音频提取
│   ├── cli.py                    # 命令行工具
│   ├── config.py                 # 配置
│   ├── diarizer.py               # 说话人分离
│   ├── enroll_voiceprints.py     # 声纹注册
│   ├── hf_utils.py               # HuggingFace 工具
│   ├── merger.py                 # 结果合并
│   ├── transcriber.py            # 语音转文字
│   ├── voiceprint_manager.py     # 声纹库管理
│   ├── examples/                 # 示例
│   └── voice_samples/            # 声纹样本
├── static/                       # 前端静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── analysis.js           # 分析页面逻辑
│       ├── archive.js            # 存档页面逻辑
│       ├── common.js             # 公共函数
│       └── enroll.js             # 注册页面逻辑
├── system.html                   # 前端主页面
├── envs/                         # Conda 环境配置文件
├── scripts/                      # 辅助脚本
│   ├── setup_env.ps1             # 环境安装脚本
│   └── push_to_github.ps1        # 推送脚本
├── docs/                         # 文档
│   └── 优化方案.md
├── uploads/                      # 上传文件目录
├── temp/                         # 临时文件目录
├── temp_analysis_uploads/        # 分析临时上传目录
├── result/                       # 检测结果输出目录
├── testvideo/                    # 测试视频存放目录
├── outputs/                      # 输出目录
├── requirements.txt              # Python 依赖
├── .env.example                  # 环境变量示例
├── .gitignore
└── README.md
```