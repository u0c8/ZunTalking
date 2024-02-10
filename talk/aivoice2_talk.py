# このファイルはもう使わない
# TODO APIを使用せずにA.I.VOICE2のGUIを操作する
# 案1 pyautoguiを使用した操作の自動化
import os
import pyautogui
import subprocess
from datetime import datetime
import re
import sys
import ctypes
import win32gui
from talker import Talker

def forground(hwnd, title):
    name = win32gui.GetWindowText(hwnd)
    if name.find(title) >= 0:

        # 最初化を戻す
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd,1) # SW_SHOWNORMAL

        ctypes.windll.user32.SetForegroundWindow(hwnd)
        return False # 列挙終了

class AIVoice2Talker(Talker):
    def __init__(self, aivoice2_path : str) -> None:
        super().__init__()
        self.aivoice2_path = aivoice2_path
        self.button_imgs = {
            "play" : "image\\aivoice2\\play_button.png",
            "write" : "image\\aivoice2\\write_button.png",
        }

    def exist(self) -> bool:
        if not os.path.isfile(self.aivoice2_path):
            print("A.I.VOICE2 Editorが見つかりませんでした")
            return False
        return True
    
    def launch(self) -> bool:
        if not self.exist():
            return False
        # 既に起動済みか確認するプロセスはSlotクラスに任せる（信頼する）
        subprocess.Popen(self.aivoice2_path)
        return True
    
    def speak(self, text : str, speaker : str | None = None, speaker_name = "noname", param_dict : dict | None = None, voice_out_dir : str | None = None, write_flag : bool = False):
        # speakの途中で呼ばれる
        def save():
            # パス整形
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            sliced_text = text[:10]
            sliced_text = re.sub(r'[\\/:*?"<>|]+', '' , sliced_text)
            path = f"{voice_out_dir}\\{timestamp}_{speaker_name}_{sliced_text}"
            # 保存
            try:
                # 合成結果をファイルに保存する
                # A.I.VOICE2のウィンドウを最前面に表示
                # TODO　処理を記述
                # 画像認識で書き出しボタンクリック
                win32gui.EnumWindows(forground, "AIVoice2")
                pyautogui.click(self.button_imgs["write"])
                # with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                #     f.write(text)
            except pyautogui.PyAutoGUIException as e:
                print("PyAutoGUIでエラー")
                print(e, file=sys.stderr)
            except Exception as e:
                print(e)
        
        if write_flag and voice_out_dir is not None:
            save()
        # 再生
        # ウィンドウを最前面に
        try:
            # win32gui.EnumWindows(forground, "A.I.VOICE2")
            title = "A.I.VOICE2"
            name = win32gui.GetWindowText(hwnd)
            if name.find(title) >= 0:
                hwnd = win32gui.FindWindow(None, name)
                win32gui.SetForegroundWindow(hwnd)
                location = pyautogui.locateOnScreen(self.button_imgs["play"])
                print('image found')
                pyautogui.click(self.button_imgs["play"])
        except pyautogui.ImageNotFoundException:
            print('ImageNotFoundException: image not found')

aivoice2 = AIVoice2Talker(r"C:\Program Files\AI\AIVoice2\AIVoice2Editor\aivoice.exe")
aivoice2.launch()
aivoice2.speak("")