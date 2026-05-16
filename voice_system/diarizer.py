#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
说话人分离器
使用Pyannote.audio进行说话人分离
"""

from pyannote.audio import Pipeline
import torch
from typing import List, Dict
import os

from .hf_utils import load_pyannote_pipeline

class Diarizer:
    """说话人分离器类"""
    
    def __init__(self, hf_token: str):
        """
        初始化分离器
        
        Args:
            hf_token: HuggingFace访问token
        """
        self.hf_token = hf_token
        self.pipeline = None
        print("🎭 初始化说话人分离器...")
    
    def load_pipeline(self):
        """加载Pyannote pipeline（延迟加载）"""
        if self.pipeline is None:
            print("正在加载Pyannote说话人分离模型...")
            try:
                self.pipeline = load_pyannote_pipeline(
                    Pipeline, "pyannote/speaker-diarization-3.1", self.hf_token
                )
                
                # 如果有GPU，使用GPU
                if torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
                    print("✅ 说话人分离模型加载完成 (GPU)")
                else:
                    print("✅ 说话人分离模型加载完成 (CPU)")
                    
            except Exception as e:
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    raise RuntimeError(
                        "HuggingFace token无效或未授权\n"
                        "请访问 https://huggingface.co/settings/tokens 创建token\n"
                        "并确保已接受模型使用条款: https://huggingface.co/pyannote/speaker-diarization-3.1"
                    )
                raise RuntimeError(f"加载说话人分离模型失败: {str(e)}")
    
    def diarize(self, audio_path: str, num_speakers: int = None) -> List[Dict]:
        """
        执行说话人分离
        
        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数量（可选，None表示自动检测）
            
        Returns:
            说话人分离结果列表，每个元素包含 start, end, speaker
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 延迟加载模型
        self.load_pipeline()
        
        print(f"开始说话人分离: {audio_path}")
        if num_speakers:
            print(f"指定说话人数量: {num_speakers}")
        else:
            print("自动检测说话人数量")
        
        try:
            # 执行分离
            # 设置更严格的参数以提高准确度
            if num_speakers:
                print(f"强制指定说话人数量: {num_speakers}")
                diarization = self.pipeline(
                    audio_path, 
                    num_speakers=num_speakers,
                    min_speakers=num_speakers,  # 最小说话人数
                    max_speakers=num_speakers   # 最大说话人数
                )
            else:
                print("自动检测说话人数量（建议手动指定以提高准确度）")
                diarization = self.pipeline(
                    audio_path,
                    min_speakers=1,
                    max_speakers=5  # 限制最大说话人数
                )
            
            # 转换为标准格式
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })
            
            # 统计说话人数量
            unique_speakers = set(seg['speaker'] for seg in segments)
            print(f"✅ 说话人分离完成，检测到 {len(unique_speakers)} 位说话人，共 {len(segments)} 个片段")
            
            return segments
            
        except Exception as e:
            raise RuntimeError(f"说话人分离失败: {str(e)}")
    
    def get_speaker_statistics(self, segments: List[Dict]) -> Dict:
        """
        获取说话人统计信息
        
        Args:
            segments: 说话人分离结果
            
        Returns:
            说话人统计信息
        """
        from collections import defaultdict
        
        stats = defaultdict(float)
        
        for seg in segments:
            speaker = seg['speaker']
            duration = seg['end'] - seg['start']
            stats[speaker] += duration
        
        return dict(stats)

