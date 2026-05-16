#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具函数
提供各种辅助功能
"""

import os
import json
from typing import List, Dict
from pathlib import Path

def format_time(seconds: float) -> str:
    """
    格式化时间为 MM:SS.mm
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串
    """
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"

def save_json(data: Dict or List, output_file: str):
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        output_file: 输出文件路径
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON已保存到: {output_file}")

def load_json(input_file: str) -> Dict or List:
    """
    加载JSON文件
    
    Args:
        input_file: 输入文件路径
        
    Returns:
        加载的数据
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_srt(results: List[Dict], output_file: str):
    """
    生成SRT字幕文件
    
    Args:
        results: 转录结果
        output_file: 输出文件路径
    """
    def format_srt_time(seconds: float) -> str:
        """格式化为SRT时间格式：HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, item in enumerate(results, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(item['start'])} --> {format_srt_time(item['end'])}\n")
            f.write(f"[{item['speaker']}] {item['text']}\n")
            f.write("\n")
    
    print(f"✅ SRT字幕已保存到: {output_file}")

def generate_html_report(results: List[Dict], output_file: str, title: str = "语音识别报告"):
    """
    生成HTML格式的报告
    
    Args:
        results: 转录结果
        output_file: 输出文件路径
        title: 报告标题
    """
    from collections import defaultdict
    
    # 统计信息
    speaker_stats = defaultdict(lambda: {'duration': 0, 'segments': 0})
    for item in results:
        duration = item['end'] - item['start']
        speaker_stats[item['speaker']]['duration'] += duration
        speaker_stats[item['speaker']]['segments'] += 1
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-item {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: #e3f2fd;
            border-radius: 5px;
        }}
        .transcript {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .segment {{
            margin-bottom: 15px;
            padding: 10px;
            border-left: 4px solid #4CAF50;
            background: #fafafa;
        }}
        .time {{
            color: #666;
            font-size: 0.9em;
            font-family: monospace;
        }}
        .speaker {{
            font-weight: bold;
            color: #1976D2;
            margin: 0 10px;
        }}
        .text {{
            margin-top: 5px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="stats">
        <h2>统计信息</h2>
"""
    
    for speaker, stats in speaker_stats.items():
        duration_min = stats['duration'] / 60
        html += f"""
        <div class="stat-item">
            <strong>{speaker}</strong><br>
            发言时长: {duration_min:.2f}分钟<br>
            发言次数: {stats['segments']}次
        </div>
"""
    
    html += """
    </div>
    
    <div class="transcript">
        <h2>转录内容</h2>
"""
    
    for item in results:
        start_time = format_time(item['start'])
        end_time = format_time(item['end'])
        html += f"""
        <div class="segment">
            <span class="time">[{start_time} → {end_time}]</span>
            <span class="speaker">{item['speaker']}</span>
            <div class="text">{item['text']}</div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML报告已保存到: {output_file}")

def check_dependencies():
    """检查所有必需的依赖是否已安装"""
    dependencies = {
        'whisper': 'openai-whisper',
        'pyannote': 'pyannote.audio',
        'torch': 'torch',
        'numpy': 'numpy',
    }
    
    missing = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ 缺少以下依赖包:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n请运行: pip install " + " ".join(missing))
        return False
    
    print("✅ 所有依赖包已安装")
    return True

