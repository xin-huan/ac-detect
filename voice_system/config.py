#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件
包含所有系统配置参数
"""

import os

class Config:
    """系统配置类"""
    
    # HuggingFace token（在 https://huggingface.co/settings/tokens 获取）
    # 方式1: 从环境变量读取（推荐）
    # 方式2: 直接在下面填写你的token（注意：不要分享这个文件）
    HF_TOKEN = os.getenv('HF_TOKEN')  # 不要在这里填写token！使用环境变量
    
    # Whisper模型大小
    # 可选: tiny, base, small, medium, large
    WHISPER_MODEL = 'medium'
    
    # 声纹匹配阈值（0-1之间，越高越严格）
    # 0.3-0.4: 宽松（可能误匹配）
    # 0.5: 默认
    # 0.6-0.7: 严格
    VOICEPRINT_THRESHOLD = 0.5  # 降低阈值以便测试
    
    # 默认说话人数量（None=自动检测，数字=强制指定）
    # 建议：如果自动检测不准，设置为实际人数
    DEFAULT_NUM_SPEAKERS = None  # 可改为 2, 3, 4 等
    
    # 音频采样率
    SAMPLE_RATE = 16000
    
    # 输出目录
    OUTPUT_DIR = 'outputs'
    
    # 声纹数据库路径（使用绝对路径，确保在任何地方运行都能找到）
    _module_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(_module_dir)
    VOICE_DB_PATH = os.path.join(_project_root, 'voice_database.pkl')
    
    # 临时文件目录
    TEMP_DIR = 'temp'
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    
    @classmethod
    def validate(cls):
        """验证配置是否有效"""
        if cls.HF_TOKEN == 'your_token_here':
            print("⚠️  警告: 未设置HuggingFace token")
            print("   请访问 https://huggingface.co/settings/tokens 创建token")
            print("   并设置环境变量: export HF_TOKEN=your_token")
            return False
        return True
    
    @classmethod
    def setup_directories(cls):
        """创建必要的目录"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)

