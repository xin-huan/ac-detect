#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
声纹管理器
管理学生声纹录入、存储和匹配
"""

from pyannote.audio import Model, Inference
import numpy as np
import pickle
import os
from typing import Optional, Dict
from pathlib import Path

from .hf_utils import load_pyannote_model

class VoiceprintManager:
    """声纹管理器类"""
    
    def __init__(self, hf_token: str, db_file: str = None):
        """
        初始化声纹管理器

        Args:
            hf_token: HuggingFace访问token
            db_file: 声纹数据库文件路径
        """
        # 统一路径：固定使用项目根目录下的 voice_database.pkl
        if db_file is None:
            # 当前文件在 D:\My code\ac-detect\voice_system\voiceprint_manager.py
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_file = os.path.join(project_root, "voice_database.pkl")

        self.hf_token = hf_token
        self.db_file = db_file
        self.model = None
        self.inference = None
        self.database = self.load_database()
        print(f"🔐 初始化声纹管理器...数据库路径: {self.db_file}")
    
    def load_model(self):
        """加载声纹提取模型（延迟加载）"""
        if self.model is None:
            print("正在加载声纹提取模型...")
            try:
                self.model = load_pyannote_model(
                    Model, "pyannote/embedding", self.hf_token
                )
                self.inference = Inference(self.model, window="whole")
                print("✅ 声纹提取模型加载完成")
            except Exception as e:
                raise RuntimeError(f"加载声纹提取模型失败: {str(e)}")
    
    def load_database(self) -> Dict:
        """加载声纹数据库"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'rb') as f:
                    database = pickle.load(f)
                print(f"✅ 加载声纹数据库，共 {len(database)} 位学生")
                return database
            except Exception as e:
                print(f"⚠️  加载声纹数据库失败: {e}")
                return {}
        else:
            print("ℹ️  声纹数据库不存在，将创建新数据库")
            return {}
    
    def save_database(self):
        """保存声纹数据库"""
        try:
            # 确保目录存在
            db_dir = os.path.dirname(self.db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            with open(self.db_file, 'wb') as f:
                pickle.dump(self.database, f)
            print(f"✅ 声纹数据库已保存: {self.db_file}")
        except Exception as e:
            raise RuntimeError(f"保存声纹数据库失败: {e}")
    
    def extract_embedding(self, audio_path: str, 
                         start: Optional[float] = None, 
                         end: Optional[float] = None) -> np.ndarray:
        """
        提取语音片段的声纹特征
        
        Args:
            audio_path: 音频文件路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            
        Returns:
            声纹特征向量
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 延迟加载模型
        self.load_model()
        
        try:
            if start is not None and end is not None:
                # 提取特定时间段的声纹
                from pydub import AudioSegment
                
                audio = AudioSegment.from_wav(audio_path)
                segment = audio[int(start * 1000):int(end * 1000)]
                
                # 保存临时文件
                temp_file = 'temp_segment.wav'
                segment.export(temp_file, format='wav')
                
                embedding = self.inference(temp_file)
                
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                # 提取整个文件的声纹
                embedding = self.inference(audio_path)
            
            return np.array(embedding)
            
        except Exception as e:
            raise RuntimeError(f"提取声纹特征失败: {str(e)}")
    
    def enroll_student(self, name: str, audio_path: str) -> bool:
        """
        录入学生声纹
        
        Args:
            name: 学生姓名
            audio_path: 语音样本文件路径
            
        Returns:
            是否成功录入
        """
        if not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在: {audio_path}")
            return False
        
        print(f"正在录入 {name} 的声纹...")
        
        try:
            # 提取声纹特征
            embedding = self.extract_embedding(audio_path)
            
            # 保存到数据库
            self.database[name] = embedding.tolist()
            self.save_database()
            
            print(f"✅ {name} 的声纹已成功录入")
            return True
            
        except Exception as e:
            print(f"❌ 录入失败: {e}")
            return False
    
    def match_speaker(self, embedding: np.ndarray, threshold: float = 0.5, debug: bool = False) -> str:
        """
        匹配说话人
        
        Args:
            embedding: 待匹配的声纹特征
            threshold: 相似度阈值（0-1）
            debug: 是否输出调试信息
            
        Returns:
            匹配的学生姓名，如果无匹配则返回"未知学生"
        """
        if not self.database:
            return "未知学生"
        
        max_sim = threshold
        best_match = None
        similarities = {}
        
        for name, stored_emb in self.database.items():
            stored_emb = np.array(stored_emb)
            
            # 计算余弦相似度
            similarity = np.dot(embedding, stored_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored_emb)
            )
            
            similarities[name] = similarity
            
            if similarity > max_sim:
                max_sim = similarity
                best_match = name
        
        # 调试输出
        if debug:
            print(f"    相似度: {', '.join([f'{name}={sim:.3f}' for name, sim in similarities.items()])}")
            if best_match:
                print(f"    最佳匹配: {best_match} (相似度={max_sim:.3f}, 阈值={threshold:.2f})")
            else:
                print(f"    无匹配 (最高相似度={max(similarities.values()):.3f}, 阈值={threshold:.2f})")
        
        return best_match if best_match else "未知学生"
    
    def list_students(self):
        """列出所有已录入的学生"""
        if not self.database:
            print("声纹数据库为空")
            return
        
        print(f"\n已录入学生列表 (共 {len(self.database)} 人):")
        print("=" * 50)
        for i, name in enumerate(self.database.keys(), 1):
            print(f"{i}. {name}")
        print("=" * 50)
    
    def delete_student(self, name: str) -> bool:
        """
        删除学生声纹
        
        Args:
            name: 学生姓名
            
        Returns:
            是否成功删除
        """
        if name not in self.database:
            print(f"❌ 学生 {name} 不存在于数据库中")
            return False
        
        del self.database[name]
        self.save_database()
        print(f"✅ 已删除学生 {name} 的声纹")
        return True
    
    def batch_enroll(self, student_dict: Dict[str, str]) -> Dict[str, bool]:
        """
        批量录入学生声纹
        
        Args:
            student_dict: {学生姓名: 音频文件路径} 的字典
            
        Returns:
            {学生姓名: 是否成功} 的字典
        """
        results = {}
        
        print(f"\n开始批量录入，共 {len(student_dict)} 位学生")
        print("=" * 50)
        
        for name, audio_path in student_dict.items():
            results[name] = self.enroll_student(name, audio_path)
        
        success_count = sum(results.values())
        print("=" * 50)
        print(f"批量录入完成: 成功 {success_count}/{len(student_dict)} 人")
        
        return results

