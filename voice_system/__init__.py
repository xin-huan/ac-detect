#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音识别系统
基于Whisper和Pyannote.audio的完整语音识别解决方案
"""

__version__ = '1.0.0'
__author__ = 'Voice Recognition Team'

from .voice_recognition_system import VoiceRecognitionSystem
from .config import Config
from .audio_extractor import AudioExtractor
from .transcriber import Transcriber
from .diarizer import Diarizer
from .voiceprint_manager import VoiceprintManager
from .merger import ResultMerger

__all__ = [
    'VoiceRecognitionSystem',
    'Config',
    'AudioExtractor',
    'Transcriber',
    'Diarizer',
    'VoiceprintManager',
    'ResultMerger',
]

