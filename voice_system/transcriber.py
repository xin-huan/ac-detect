#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音转录器
使用Whisper将语音转换为文字
"""

import whisper
from typing import List, Dict
import os

class Transcriber:
    """语音转录器类"""
    
    def __init__(self, model_size: str = 'medium'):
        """
        初始化转录器
        
        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
        """
        self.model_size = model_size
        self.model = None
        print(f"[INIT] 初始化Whisper模型 (size={model_size})...")
    
    def load_model(self):
        """加载Whisper模型（延迟加载）"""
        if self.model is None:
            print(f"正在加载Whisper {self.model_size} 模型...")
            self.model = whisper.load_model(self.model_size)
            print("✅ Whisper模型加载完成")
    
    def transcribe(self, audio_path: str, language: str = 'zh') -> List[Dict]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh/en等)
            
        Returns:
            转录结果列表，每个元素包含 start, end, text, 以及词级别时间戳
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 延迟加载模型
        self.load_model()
        
        print(f"开始转录音频: {audio_path}")
        
        try:
            # 执行转录，启用VAD和词级时间戳
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                word_timestamps=True,  # 启用词级时间戳
                initial_prompt="以下是普通话的句子。"  # 提示使用简体中文
            )
            
            segments = result['segments']
            
            print(f"✅ 转录完成，共 {len(segments)} 个片段")
            
            # 标准化输出格式并转换为简体中文
            standardized_segments = []
            for seg in segments:
                text = seg['text'].strip()
                # 简单的繁简转换
                text = self._convert_to_simplified(text)
                
                # 保留词级别时间戳
                words_with_timestamps = []
                if 'words' in seg:
                    for word_info in seg['words']:
                        words_with_timestamps.append({
                            'word': self._convert_to_simplified(word_info['word'].strip()),
                            'start': word_info['start'],
                            'end': word_info['end']
                        })

                standardized_segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': text,
                    'words': words_with_timestamps
                })
            
            return standardized_segments
            
        except Exception as e:
            raise RuntimeError(f"转录失败: {str(e)}")
    
    def _convert_to_simplified(self, text: str) -> str:
        """
        繁体转简体（基础版本）
        """
        # 常用繁简对照表
        trans_map = {
            '麼': '么', '師': '师', '忙': '忙', '呢': '呢', '實': '实',
            '怎': '怎', '說': '说', '裡': '里', '讀': '读', '書': '书',
            '寫': '写', '字': '字', '溜': '溜', '彎': '弯', '飯': '饭',
            '覺': '觉', '個': '个', '這': '这', '為': '为', '們': '们',
            '來': '来', '對': '对', '會': '会', '還': '还', '學': '学',
            '過': '过', '時': '时', '間': '间', '點': '点', '見': '见',
            '現': '现', '開': '开', '關': '关', '問': '问', '題': '题',
            '應': '应', '該': '该', '樣': '样', '聽': '听', '講': '讲',
            '話': '话', '認': '认', '識': '识', '覺': '觉', '讓': '让',
            '請': '请', '謝': '谢', '買': '买', '賣': '卖', '錢': '钱',
        }
        
        result = []
        for char in text:
            result.append(trans_map.get(char, char))
        return ''.join(result)
    
    def transcribe_with_word_timestamps(self, audio_path: str, language: str = 'zh') -> Dict:
        """
        转录音频并提供词级时间戳
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            完整的转录结果（包含词级时间戳）
        """
        self.load_model()
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            word_timestamps=True
        )
        
        return result

