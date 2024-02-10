import subprocess
import os
from talk.talker import Talker
from datetime import datetime
import re

class AquesTalk(Talker):
    def __init__(self, aquestalk_path : str) -> None:
        super().__init__()
        self.aquestalk_path = aquestalk_path

    def exist(self) -> bool:
        if not os.path.isfile(self.aquestalk_path):
            print("AquesTalkPlayerが見つかりませんでした")
            return False
        return True
    
    def launch(self) -> bool:
        # AquesTalkPlayerは起動不要
        if not self.exist():
            return False
        return True

    def speak(self, text : str, preset : str, speaker_name = "noname", param_dict : None = None, talk_flag : bool = True, voice_out_dir : str | None = None, write_flag : bool = False) -> None:
        def save():
            # パス整形
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            sliced_text = text[:10]
            sliced_text = re.sub(r'[\\/:*?"<>|]+', '' , sliced_text)
            path = f"{voice_out_dir}\\{timestamp}_{speaker_name}_{sliced_text}"
            # 保存
            try:
                cmd = ["start", self.aquestalk_path, "/T", text, "/P", preset, "/W", f"{path}.wav"]
                subprocess.run(" ".join(cmd), shell=True)
                with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                    f.write(text)
                print(f"Voice save to {path}")
            except Exception as e:
                print(e)
        if not self.exist():
            return
        if write_flag and voice_out_dir is not None:
            save()
        if talk_flag:
            print(f"AquesTalkPlayer: {speaker_name} talking...")
            cmd = ["start", self.aquestalk_path, "/T", text, "/P", preset]
            subprocess.run(" ".join(cmd), shell=True)