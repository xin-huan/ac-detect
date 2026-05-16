#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行接口
提供便捷的命令行操作
"""

import argparse
import os
import sys

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description='语音识别系统 - 将视频/音频转录为带说话人标识的文字'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # process命令
    process_parser = subparsers.add_parser('process', help='处理视频或音频文件')
    process_parser.add_argument('input', help='输入文件路径（视频或音频）')
    process_parser.add_argument('-o', '--output', help='输出文件路径')
    process_parser.add_argument('--token', help='HuggingFace token')
    process_parser.add_argument('--voiceprint', action='store_true', 
                               help='启用声纹匹配')
    process_parser.add_argument('--speakers', type=int, 
                               help='指定说话人数量（可选）')
    
    # enroll命令
    enroll_parser = subparsers.add_parser('enroll', help='录入学生声纹')
    enroll_parser.add_argument('name', help='学生姓名')
    enroll_parser.add_argument('audio', help='音频文件路径')
    enroll_parser.add_argument('--token', help='HuggingFace token')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出已录入的学生')
    
    # delete命令
    delete_parser = subparsers.add_parser('delete', help='删除学生声纹')
    delete_parser.add_argument('name', help='学生姓名')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # 导入系统（延迟导入以加快启动速度）
    from .voice_recognition_system import VoiceRecognitionSystem
    from .voiceprint_manager import VoiceprintManager
    from .config import Config
    
    # 获取token
    token = args.token if hasattr(args, 'token') and args.token else os.getenv('HF_TOKEN')
    
    if args.command == 'process':
        if not token:
            print("❌ 错误: 未提供HuggingFace token")
            print("请使用 --token 参数或设置环境变量 HF_TOKEN")
            sys.exit(1)
        
        # 处理文件
        system = VoiceRecognitionSystem(token)
        
        if args.input.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # 视频文件
            system.process_video(
                args.input,
                output_file=args.output,
                use_voiceprint=args.voiceprint,
                num_speakers=args.speakers
            )
        else:
            # 音频文件
            system.process_audio(
                args.input,
                output_file=args.output,
                use_voiceprint=args.voiceprint,
                num_speakers=args.speakers
            )
    
    elif args.command == 'enroll':
        if not token:
            print("❌ 错误: 未提供HuggingFace token")
            sys.exit(1)
        
        # 录入声纹
        config = Config()
        mgr = VoiceprintManager(token, config.VOICE_DB_PATH)
        mgr.enroll_student(args.name, args.audio)
    
    elif args.command == 'list':
        # 列出学生
        config = Config()
        if not os.path.exists(config.VOICE_DB_PATH):
            print("声纹数据库不存在")
        else:
            import pickle
            with open(config.VOICE_DB_PATH, 'rb') as f:
                db = pickle.load(f)
            
            if not db:
                print("声纹数据库为空")
            else:
                print(f"\n已录入学生列表 (共 {len(db)} 人):")
                print("=" * 50)
                for i, name in enumerate(db.keys(), 1):
                    print(f"{i}. {name}")
                print("=" * 50)
    
    elif args.command == 'delete':
        # 删除声纹
        config = Config()
        if not os.path.exists(config.VOICE_DB_PATH):
            print("声纹数据库不存在")
        else:
            import pickle
            with open(config.VOICE_DB_PATH, 'rb') as f:
                db = pickle.load(f)
            
            if args.name not in db:
                print(f"❌ 学生 {args.name} 不存在于数据库中")
            else:
                del db[args.name]
                with open(config.VOICE_DB_PATH, 'wb') as f:
                    pickle.dump(db, f)
                print(f"✅ 已删除学生 {args.name} 的声纹")

if __name__ == '__main__':
    main()

