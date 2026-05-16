#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础使用示例
演示如何使用语音识别系统处理视频
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_system import VoiceRecognitionSystem

def main():
    """基础使用示例"""
    
    # 1. 从环境变量中获取HuggingFace token
    #   - 程序会首先尝试从 .env 文件加载
    #   - 如果 .env 文件不存在，则会尝试从系统环境变量加载
    hf_token = os.getenv('HF_TOKEN')
    
    if not hf_token or hf_token == 'your_hugging_face_token_here':
        print("❌ 请设置HuggingFace token")
        print("   1. 在 voice_system/examples/ 目录下创建一个 .env 文件")
        print("   2. 在文件中添加一行: HF_TOKEN='your_actual_token'")
        return
    
    # 2. 初始化系统
    system = VoiceRecognitionSystem(hf_token)
    
    # 3. 处理视频文件
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 拼接正确的视频文件路径
    video_path = os.path.join(script_dir, '../../test1.mp4')  # 根据脚本目录拼接路径

    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        print("   请修改 video_path 变量为实际的视频文件路径")
        return
    
    # 处理视频（启用声纹匹配）
    # 提示：如果知道说话人数量，强烈建议指定，因为自动检测在某些复杂场景下可能不准。
    
    # --- 模式1: 自动检测说话人数量 (当你不确定有几个人时使用) ---
    # results = system.process_video(
    #     video_path,
    #     output_file='output/transcript.txt',
    #     use_voiceprint=True
    # )

    # --- 模式2: 强制指定说话人数量 (当你确定人数时使用，可以显著提高准确度) ---
    results = system.process_video(
        video_path,
        output_file='output/transcript.txt',
        use_voiceprint=True,  # 启用声纹匹配
        num_speakers=2        # 在此指定说话人数量
    )
    
    # 4. 打印部分结果
    print("\n前5个片段:")
    print("=" * 70)
    for item in results[:5]:
        print(f"[{system.format_time(item['start'])}-->{system.format_time(item['end'])}]")
        print(f"  说话人: {item['speaker']}")
        print(f"  内容: {item['text']}")
        print()

if __name__ == '__main__':
    main()

