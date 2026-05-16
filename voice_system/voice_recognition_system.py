#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音识别系统主控制器
整合所有模块，提供统一的接口
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
from pyannote.audio import Pipeline
import soundfile as sf
import numpy as np

from .config import Config
from .hf_utils import load_pyannote_pipeline
from .audio_extractor import AudioExtractor
from .transcriber import Transcriber
from .diarizer import Diarizer
from .voiceprint_manager import VoiceprintManager
from .merger import ResultMerger

class VoiceRecognitionSystem:
    """语音识别系统主类"""
    
    def __init__(self, hf_token: str, config: Config = None):
        """
        初始化系统
        
        Args:
            hf_token: HuggingFace访问token
            config: 配置对象（可选）
        """
        self.config = config or Config()
        self.hf_token = hf_token
        
        # 初始化各个模块
        print("=" * 70)
        print("语音识别系统初始化")
        print("=" * 70)
        
        self.audio_extractor = AudioExtractor()
        self.transcriber = Transcriber(self.config.WHISPER_MODEL)
        self.diarizer = Diarizer(hf_token)
        
        print("🎤 初始化VAD模型以进行静音检测...")
        try:
            self.vad_pipeline = load_pyannote_pipeline(
                Pipeline, "pyannote/voice-activity-detection", self.hf_token
            )
            print("✅ VAD模型加载完成")
        except Exception as e:
            print(f"⚠️  VAD模型加载失败: {e}。将跳过静音裁剪步骤。")
            self.vad_pipeline = None

        self.voiceprint_mgr = VoiceprintManager(
            hf_token, 
            self.config.VOICE_DB_PATH
        )
        self.merger = ResultMerger()
        
        # 创建必要的目录
        self.config.setup_directories()
        
        print("=" * 70)
        print("[OK] 系统初始化完成")
        print("=" * 70 + "\n")
    
    def process_video(self, video_path: str, 
                     output_file: Optional[str] = None,
                     use_voiceprint: bool = False,
                     num_speakers: Optional[int] = None,
                     merge_consecutive: bool = True) -> List[Dict]:
        """
        处理视频文件的完整流程
        
        Args:
            video_path: 视频文件路径
            output_file: 输出文件路径（可选）
            use_voiceprint: 是否使用声纹匹配
            num_speakers: 说话人数量（None表示自动检测）
            merge_consecutive: 是否合并连续的相同说话人片段
            
        Returns:
            处理结果列表
        """
        print("\n" + "=" * 70)
        print(f"[VIDEO] 开始处理视频: {video_path}")
        print("=" * 70 + "\n")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        try:
            # 1. 提取音频
            print("[1/5] 提取音频...")
            audio_path = self._extract_audio(video_path)
            
            # 新增步骤: 使用VAD裁剪前导静音
            audio_path = self._trim_leading_silence(audio_path)
            
            # 2. 语音转文字
            print("\n[2/5] 语音转文字...")
            transcripts = self.transcriber.transcribe(audio_path)
            
            # 调试：显示前几个转录片段
            print("\n转录片段详情:")
            for i, seg in enumerate(transcripts[:5], 1):
                print(f"  片段{i}: [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
            
            # 3. 说话人分离
            print("\n[3/5] 说话人分离...")
            diarization = self.diarizer.diarize(audio_path, num_speakers)
            
            # 调试：显示前几个说话人片段
            print("\n说话人分离详情:")
            for i, seg in enumerate(diarization[:5], 1):
                print(f"  片段{i}: [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['speaker']}")
            
            # 4. 合并结果
            print("\n[4/5] 合并结果...")
            results = self.merger.merge(transcripts, diarization)
            
            # 可选：合并连续片段
            if merge_consecutive:
                results = self.merger.merge_consecutive_segments(results)
            
            # 5. 声纹匹配（可选）
            if use_voiceprint:
                print("\n[5/5] 声纹匹配...")
                results = self._match_speakers(results, audio_path)
            else:
                print("\n[5/5] 跳过声纹匹配")
            
            # 6. 保存结果
            print("\n保存结果...")
            if output_file is None:
                output_file = self._generate_output_filename(video_path)
            
            self.save_results(results, output_file)
            
            # 显示统计信息
            self._print_statistics(results)
            
            print("\n" + "=" * 70)
            print("[OK] 处理完成！")
            print("=" * 70 + "\n")
            
            return results
            
        except Exception as e:
            print(f"\n❌ 处理失败: {str(e)}")
            raise
    
    def _trim_leading_silence(self, audio_path: str, silence_threshold_s: float = 0.5) -> str:
        """
        使用VAD检测并裁剪音频文件的前导静音。
        如果检测到明显的静音，会创建一个新的临时文件。
        否则，返回原始音频路径。
        """
        if not self.vad_pipeline:
            return audio_path

        print("\n🎤 应用VAD裁剪前导静音...")
        try:
            vad_result = self.vad_pipeline(audio_path)
            
            # 找到第一个语音片段的开始时间
            speech_segments = list(vad_result.get_timeline().support())
            if not speech_segments:
                print("  ⚠️ VAD未检测到任何语音活动，使用原始音频。")
                return audio_path

            first_speech_start = speech_segments[0].start
            
            if first_speech_start > silence_threshold_s:
                print(f"  检测到 {first_speech_start:.2f}s 的前导静音，正在裁剪...")
                
                waveform, sample_rate = sf.read(audio_path)
                
                start_frame = int(first_speech_start * sample_rate)
                trimmed_waveform = waveform[start_frame:]
                
                # 为裁剪后的文件创建新路径
                original_filename = Path(audio_path).stem
                trimmed_audio_path = os.path.join(
                    self.config.TEMP_DIR,
                    f"{original_filename}_trimmed.wav"
                )
                
                sf.write(trimmed_audio_path, trimmed_waveform, sample_rate)
                print(f"  ✅ 已保存裁剪后的音频到: {trimmed_audio_path}")
                return trimmed_audio_path
            else:
                print("  未检测到明显的前导静音，使用原始音频。")
                return audio_path

        except Exception as e:
            print(f"  ⚠️ VAD预处理失败: {e}。使用原始音频。")
            return audio_path

    def process_audio(self, audio_path: str,
                     output_file: Optional[str] = None,
                     use_voiceprint: bool = False,
                     num_speakers: Optional[int] = None) -> List[Dict]:
        """
        直接处理音频文件
        
        Args:
            audio_path: 音频文件路径
            output_file: 输出文件路径
            use_voiceprint: 是否使用声纹匹配
            num_speakers: 说话人数量
            
        Returns:
            处理结果列表
        """
        print("\n" + "=" * 70)
        print(f"🎵 开始处理音频: {audio_path}")
        print("=" * 70 + "\n")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        try:
            # 1. 语音转文字
            print("[1/3] 语音转文字...")
            transcripts = self.transcriber.transcribe(audio_path)
            
            # 2. 说话人分离
            print("\n[2/3] 说话人分离...")
            diarization = self.diarizer.diarize(audio_path, num_speakers)
            
            # 3. 合并结果
            print("\n[3/3] 合并结果...")
            results = self.merger.merge(transcripts, diarization)
            
            # 声纹匹配（可选）
            if use_voiceprint:
                print("\n声纹匹配...")
                results = self._match_speakers(results, audio_path)
            
            # 保存结果
            if output_file is None:
                output_file = self._generate_output_filename(audio_path)
            
            self.save_results(results, output_file)
            
            # 显示统计信息
            self._print_statistics(results)
            
            print("\n" + "=" * 70)
            print("[OK] 处理完成！")
            print("=" * 70 + "\n")
            
            return results
            
        except Exception as e:
            print(f"\n❌ 处理失败: {str(e)}")
            raise
    
    def _extract_audio(self, video_path: str) -> str:
        """提取音频"""
        output_path = os.path.join(
            self.config.TEMP_DIR,
            Path(video_path).stem + '.wav'
        )
        return self.audio_extractor.extract(
            video_path,
            output_path,
            self.config.SAMPLE_RATE
        )
    
    def _match_speakers(self, results: List[Dict], audio_path: str) -> List[Dict]:
        """将speaker ID替换为学生姓名"""
        if not self.voiceprint_mgr.database:
            print("⚠️  声纹数据库为空，跳过匹配")
            return results
        
        speaker_cache = {}
        matched_count = 0
        
        for item in results:
            speaker_id = item['speaker']
            
            if speaker_id not in speaker_cache:
                try:
                    # 提取该说话人的声纹
                    embedding = self.voiceprint_mgr.extract_embedding(
                        audio_path,
                        item['start'],
                        item['end']
                    )
                    
                    # 匹配学生（启用调试输出）
                    name = self.voiceprint_mgr.match_speaker(
                        embedding,
                        self.config.VOICEPRINT_THRESHOLD,
                        debug=True  # 输出相似度
                    )
                    
                    speaker_cache[speaker_id] = name
                    
                    if name != "未知学生":
                        matched_count += 1
                        print(f"  {speaker_id} → {name}")
                    
                except Exception as e:
                    print(f"  ⚠️  匹配 {speaker_id} 失败: {e}")
                    speaker_cache[speaker_id] = speaker_id
            
            item['speaker'] = speaker_cache[speaker_id]
        
        print(f"[OK] 声纹匹配完成: {matched_count}/{len(speaker_cache)} 位说话人被识别")
        return results
    
    def save_results(self, results: List[Dict], output_file: str):
        """保存结果为可读文本"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("语音识别结果\n")
                f.write("=" * 70 + "\n\n")
                
                for item in results:
                    start_time = self.format_time(item['start'])
                    end_time = self.format_time(item['end'])
                    f.write(f"[{start_time}-->{end_time}] ")
                    f.write(f"[{item['speaker']}] ")
                    f.write(f"{item['text']}\n")
            
            print(f"[OK] 结果已保存到: {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"保存结果失败: {e}")
    
    def _generate_output_filename(self, input_path: str) -> str:
        """生成输出文件名"""
        basename = Path(input_path).stem
        output_file = os.path.join(
            self.config.OUTPUT_DIR,
            f"{basename}_transcript.txt"
        )
        return output_file
    
    def _print_statistics(self, results: List[Dict]):
        """打印统计信息"""
        stats = self.merger.get_speaker_statistics(results)
        
        print("\n" + "=" * 70)
        print("[STATS] 统计信息")
        print("=" * 70)
        
        for speaker, info in stats.items():
            duration_min = info['duration'] / 60
            print(f"\n{speaker}:")
            print(f"  发言时长: {duration_min:.2f} 分钟")
            print(f"  发言次数: {info['segments']} 次")
            print(f"  文字数量: {info['text_length']} 字")
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """格式化时间"""
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m:02d}:{s:05.2f}"

