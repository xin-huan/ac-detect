#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
结果合并器
将转录结果和说话人分离结果合并
"""

from typing import List, Dict

class ResultMerger:
    """结果合并器类"""
    
    @staticmethod
    def merge(transcripts: List[Dict], diarization: List[Dict]) -> List[Dict]:
        """
        将转录和说话人信息合并 (新版，基于词级时间戳)
        
        Args:
            transcripts: Whisper转录结果 (包含词级时间戳)
            diarization: 说话人分离结果 [{start, end, speaker}, ...]
            
        Returns:
            合并后的结果 [{start, end, speaker, text}, ...]
        """
        if not transcripts or 'words' not in transcripts[0]:
            print("⚠️  转录结果为空或不包含词级时间戳，无法进行精确合并")
            return []
        
        if not diarization:
            print("⚠️  说话人分离结果为空")
            return []

        # 1. 创建一个包含所有词的扁平列表
        all_words = []
        for segment in transcripts:
            all_words.extend(segment.get('words', []))

        if not all_words:
            print("⚠️  未在转录结果中找到任何词")
            return []

        results = []
        # 2. 以说话人片段为基准进行合并
        for diar_seg in diarization:
            diar_start = diar_seg['start']
            diar_end = diar_seg['end']
            speaker = diar_seg['speaker']
            
            # 3. 找到时间戳在此区间内的所有词
            segment_words = []
            for word in all_words:
                word_start = word['start']
                word_end = word['end']
                
                # 定义一个更宽松的重叠条件，确保不会丢失词语
                # 词的中心点在说话人片段内即可
                word_mid_point = (word_start + word_end) / 2
                if diar_start <= word_mid_point < diar_end:
                    segment_words.append(word['word'])
            
            if segment_words:
                # 4. 拼接文本并创建新片段
                text = "".join(segment_words)
                
                results.append({
                    'start': diar_start,
                    'end': diar_end,
                    'speaker': speaker,
                    'text': text.strip()
                })
        
        print(f"✅ 结果合并完成，共 {len(results)} 个片段")
        return results
    
    @staticmethod
    def _find_speaker(start: float, end: float, 
                     diarization: List[Dict]) -> str:
        """
        为给定时间段找到对应的说话人
        
        Args:
            start: 开始时间
            end: 结束时间
            diarization: 说话人分离结果
            
        Returns:
            说话人标识
        """
        # 计算与每个说话人片段的重叠程度
        max_overlap = 0
        best_speaker = "未知"
        
        trans_duration = end - start
        
        for diar_seg in diarization:
            diar_start = diar_seg['start']
            diar_end = diar_seg['end']
            
            # 计算重叠区间
            overlap_start = max(start, diar_start)
            overlap_end = min(end, diar_end)
            
            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                
                # 计算重叠比例（相对于转录片段的长度）
                overlap_ratio = overlap / trans_duration if trans_duration > 0 else 0
                
                if overlap_ratio > max_overlap:
                    max_overlap = overlap_ratio
                    best_speaker = diar_seg['speaker']
        
        return best_speaker
    
    @staticmethod
    def merge_consecutive_segments(results: List[Dict], 
                                   max_gap: float = 1.0) -> List[Dict]:
        """
        合并连续的相同说话人片段
        
        Args:
            results: 合并后的结果
            max_gap: 最大允许间隔（秒）
            
        Returns:
            合并后的结果
        """
        if not results:
            return []
        
        merged = []
        current = results[0].copy()
        
        for i in range(1, len(results)):
            next_seg = results[i]
            
            # 检查是否可以合并
            gap = next_seg['start'] - current['end']
            same_speaker = next_seg['speaker'] == current['speaker']
            
            if same_speaker and gap <= max_gap:
                # 合并
                current['end'] = next_seg['end']
                current['text'] += ' ' + next_seg['text']
            else:
                # 不合并，保存当前段并开始新段
                merged.append(current)
                current = next_seg.copy()
        
        # 添加最后一段
        merged.append(current)
        
        print(f"✅ 合并连续片段: {len(results)} → {len(merged)} 个片段")
        return merged
    
    @staticmethod
    def get_speaker_statistics(results: List[Dict]) -> Dict:
        """
        统计各说话人的发言情况
        
        Args:
            results: 合并后的结果
            
        Returns:
            统计信息 {speaker: {duration, segments, text_length}}
        """
        from collections import defaultdict
        
        stats = defaultdict(lambda: {
            'duration': 0.0,
            'segments': 0,
            'text_length': 0
        })
        
        for seg in results:
            speaker = seg['speaker']
            duration = seg['end'] - seg['start']
            text_length = len(seg['text'])
            
            stats[speaker]['duration'] += duration
            stats[speaker]['segments'] += 1
            stats[speaker]['text_length'] += text_length
        
        return dict(stats)

