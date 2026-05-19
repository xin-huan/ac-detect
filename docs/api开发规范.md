# 📁 项目目录与 API 开发规范

本项目采用统一的接口管理结构，所有接口（API）文件集中放在根目录下的 **`api/` 文件夹** 中，便于多人协作和统一维护。

---

## 🧱 一、项目结构示例

```
ac-detect/
│
├── app.py                     # Flask 主程序入口（这个后面我写）
│
├── api/                       # 所有后端 API 接口文件
│   ├── __init__.py
│   ├── voice_api.py           # 声纹识别相关接口
│
├── voice_system/              # 声纹识别模块核心逻辑（特征提取、数据库管理等）
│   ├── voiceprint_manager.py
│   └── ...
            # 前端页面模板（HTML）
```

---

## 🚀 二、API 文件规范

每个功能模块由 **独立的 API 文件** 管理，例如：

* `voice_api.py` → 声纹识别（录入、识别）

---

### 示例：`api/voice_api.py`

```python
from flask import Blueprint, request, jsonify
from voice_system import VoiceRecognitionSystem

voice_bp = Blueprint('voice_api', __name__)

@voice_bp.route('/enroll', methods=['POST'])
def enroll_voice():
    # 声纹录入逻辑
    ...
    return jsonify({"message": "enrolled successfully"})
```


## 🔗 三、接口访问示例

| 模块   | 接口路径                   | 示例              |
| ---- | ---------------------- | --------------- |
| 声纹识别 | `/api/voice/enroll`    | POST 上传音频录入声纹   |

---

## 🧭 四、开发注意事项

1. 所有接口函数都返回 `jsonify(...)` 格式的响应；
2. 路由命名简洁、统一，建议使用动词（如 `/enroll`, `/detect`, `/recognize`）；
3. API 内部逻辑调用各自系统模块中的类与函数；
4. 开发完接口后，请在写好接口路径与功能说明。

---

> 📌 统一管理接口文件，方便后期维护、测试与部署。
> 如需新增模块，请先在 `api/` 中新建对应文件。



## 其他

system.html是现有页面
