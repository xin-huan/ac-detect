#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
声纹录入脚本
用于录入学生的声纹样本
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
dotenv_path = os.path.join(os.path.dirname(__file__), 'examples', '.env')
load_dotenv(dotenv_path)

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_system import VoiceRecognitionSystem

def main():
    # 从环境变量中加载 HF_TOKEN
    token = os.getenv('HF_TOKEN')
    
    if not token or token == 'your_hugging_face_token_here':
        print("❌ 请设置HuggingFace token")
        print("   1. 在 voice_system/examples/ 目录下创建一个 .env 文件")
        print("   2. 在文件中添加一行: HF_TOKEN='your_actual_token'")
        return
    
    print("=" * 70)
    print("声纹录入系统")
    print("=" * 70)
    
    # 初始化系统
    print("\n初始化系统...")
    system = VoiceRecognitionSystem(hf_token=token)
    
    # 定义学生和对应的声纹样本文件
    # 修改这里：填入你的学生姓名和对应的音频文件路径
    students = {
        'Papi': 'voice_samples/papi.wav',
        '罗翔': 'voice_samples/luoxiang1.wav',
        # 添加更多学生...
    }
    
    print(f"\n准备录入 {len(students)} 位学生的声纹")
    print("=" * 70)
    
    # 批量录入
    results = system.voiceprint_mgr.batch_enroll(students)
    
    # 显示结果
    print("\n" + "=" * 70)
    print("录入结果汇总:")
    print("=" * 70)
    
    success_count = sum(results.values())
    for name, success in results.items():
        status = "[OK] 成功" if success else "[FAIL] 失败"
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 70)
    print(f"总计: {success_count}/{len(students)} 人录入成功")
    print("=" * 70)
    
    # 显示已录入的学生列表
    print("\n当前声纹数据库中的学生:")
    system.voiceprint_mgr.list_students()
    
    print("\n声纹录入完成！")
    print("现在可以在 examples/basic_usage.py 中设置 use_voiceprint=True 来使用声纹匹配")

if __name__ == '__main__':
    main()

