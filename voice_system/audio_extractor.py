#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频提取器
从视频文件中提取音频
"""

import subprocess
import os
from pathlib import Path
from typing import Optional

class AudioExtractor:
    """音频提取器类"""
    
    @staticmethod
    def extract(video_path: str, output_path: Optional[str] = None, 
                sample_rate: int = 16000) -> str:
        """
        从视频提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径（可选）
            sample_rate: 采样率（默认16000Hz）
            
        Returns:
            输出音频文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 如果未指定输出路径，使用相同文件名
        if output_path is None:
            output_path = Path(video_path).stem + '.wav'
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-i', video_path,          # 输入文件
            '-ar', str(sample_rate),   # 采样率
            '-ac', '1',                # 单声道
            '-vn',                     # 不处理视频
            '-y',                      # 覆盖输出文件
            output_path
        ]
        
        try:
            # 执行命令，隐藏输出
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"音频提取失败，未生成输出文件: {output_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise RuntimeError(f"提取的音频文件为空: {output_path}")
            
            print(f"✅ 音频提取成功: {output_path} ({file_size / 1024 / 1024:.2f} MB)")
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"FFmpeg执行失败: {e.stderr}\n"
                f"请确保已安装FFmpeg: https://ffmpeg.org/download.html"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "找不到FFmpeg命令，请先安装FFmpeg\n"
                "Windows: 下载并添加到PATH\n"
                "Linux: sudo apt install ffmpeg\n"
                "Mac: brew install ffmpeg"
            )
    
    @staticmethod
    def check_ffmpeg() -> bool:
        """检查FFmpeg是否可用"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

