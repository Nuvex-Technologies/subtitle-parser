#!/usr/bin/env python3
# このスクリプトは複数のアニメエピソード（MKVファイル）から特定の時間範囲の字幕を抽出・結合し、1つのASSファイルとして保存します。
# 必要条件: mkvmerge, mkvextract（MKVToolNixに含まれる）をインストールしてください。

import subprocess
import re
from datetime import datetime, timedelta
import os

# 「例のクリップは、これらがタイムスタンプであり、ビデオのセクションの開始時刻と終了時刻を示しています。順番は逆ではなく、前後の順序で記載されていますので、実際のビデオの時間を示しています。」
clips = [
    ("S01E25", "00:13:10", "00:14:29"),
    ("S01E25", "00:15:07", "00:15:40"), 
    ("S01E25", "00:22:31", "00:22:50"),
    ("S01E26", "00:01:43", "00:03:08"),
    ("S01E26", "00:17:50", "00:18:08"),
    ("S01E26", "00:18:41", "00:18:46"),
    ("S01E26", "00:19:01", "00:21:22")
]

# 例のエピソード
episode_files = {
    "S01E25": "Frieren Beyond Journey's End - S01e25 (Bd Remux 1080P Avc Flac Aac) [Dual Audio] [Pmr].mkv",
    "S01E26": "Frieren Beyond Journey's End - S01e26 (Bd Remux 1080P Avc Flac Aac) [Dual Audio] [Pmr].mkv"
}

def time_to_seconds(time_str):
    if '.' in time_str:
        time_str = time_str.split('.')[0]
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    return timedelta(hours=time_obj.hour, minutes=time_obj.minute, seconds=time_obj.second).total_seconds()

def extract_subtitles():
    current_time = 0
    output_subs = []
    output_subs.extend([
        '[Script Info]',
        'ScriptType: v4.00+',
        'PlayResX: 1920',
        'PlayResY: 1080',
        'WrapStyle: 0',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
        ''
    ])
    
    for episode, start_time, end_time in clips:
        mkv_info = subprocess.check_output(['mkvmerge', '-i', episode_files[episode]], text=True)
        track_id = None
        for line in mkv_info.split('\n'):
            if 'subtitles' in line.lower():
                track_id = re.search(r'Track ID (\d+)', line).group(1)
                break
        
        if not track_id:
            print(f"Could not find subtitle track in {episode}")
            continue
            
        start_seconds = time_to_seconds(start_time)
        end_seconds = time_to_seconds(end_time)
        duration = end_seconds - start_seconds

        subprocess.run([
            'mkvextract', episode_files[episode], 
            'tracks', f'{track_id}:temp.ass'
        ])
        
        with open('temp.ass', 'r', encoding='utf-8') as f:
            subs = f.read()
        
        for line in subs.split('\n'):
            if line.startswith('Dialogue:'):
                fields = line.split(',', 9)
                if len(fields) >= 10:
                    start_time_str = fields[1].strip()
                    end_time_str = fields[2].strip()
                    
                    sub_start = time_to_seconds(start_time_str)
                    sub_end = time_to_seconds(end_time_str)
                    
                    if sub_start >= start_seconds and sub_end <= end_seconds:
                        new_start = sub_start - start_seconds + current_time
                        new_end = sub_end - start_seconds + current_time
                        
                        new_start_str = str(timedelta(seconds=int(new_start)))
                        new_end_str = str(timedelta(seconds=int(new_end)))
                        
                        new_line = f"Dialogue: 0,{new_start_str}.00,{new_end_str}.00,Default,,0,0,0,,{fields[9]}"
                        output_subs.append(new_line)
        
        current_time += duration
        
    with open('output.ass', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_subs))
    
    if os.path.exists('temp.ass'):
        subprocess.run(['rm', 'temp.ass'])

if __name__ == '__main__':
    extract_subtitles()
