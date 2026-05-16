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
│
├── app.py                     # Flask 主程序入口（这个后面我写）
│
├── api/                       # 所有后端 API 接口文件
│   ├── __init__.py
│   ├── voice_api.py           # 声纹识别相关接口
│
├── envs/                      # 环境
│   ├── 
│   └── 
├── insightface-master/          # 人脸识别模块核心逻辑（特征提取、数据库管理等）
    ├── face_database/            
│   ├──face_vectors.pkl         
│    
├── result/              # 识别结果
│   ├─
├── testvideo/              # 检测的视频
│   ├─
├── ultralytics/              # 行为识别模块核心逻辑（目标检测）
│   ├─
├── voice_system/              # 声纹识别模块核心逻辑（特征提取、数据库管理等）
│   ├── 
            # 前端页面模板（HTML）
```