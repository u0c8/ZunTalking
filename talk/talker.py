from abc import ABCMeta, abstractmethod
import os
import time
import pyautogui
import subprocess
from datetime import datetime
import re
import sys
import ctypes
import win32gui
import math
import pyperclip

class Talker(metaclass = ABCMeta):
    @abstractmethod
    def exist() -> bool:
        pass
    @abstractmethod
    def launch() -> bool:
        pass
    @abstractmethod
    def speak(text : str, speaker : int | str = 0, speaker_name = "noname"):
        # speakerはAquesTalkのみ文字列指定
        # 最低構成でしゃべらせる
        pass

class AIVoice2Talker(Talker):
    def __init__(self, aivoice2_path : str) -> None:
        super().__init__()
        self.aivoice2_path = aivoice2_path
        self.button_imgs = {
            "play" : "image\\aivoice2\\play_button.png",
            "write" : "image\\aivoice2\\write_button.png",
            "stop" : "image\\aivoice2\\stop_button.png",
            "sentence_next" : "image\\aivoice2\\sentence_next.png",
            "sentence_prev" : "image\\aivoice2\\sentence_prev.png", 
            "all_play" : "image\\aivoice2\\all_play_button.png",
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
            def write_emulate(hwnd, title):
                # 名称をウィンドウ一覧から検索
                name = win32gui.GetWindowText(hwnd)
                if name.find(title) >= 0:
                    # 検索した名称からハンドラ取得
                    hwnd = win32gui.FindWindow(None, name)
                    # ウィンドウを最前面に
                    win32gui.SetForegroundWindow(hwnd)
                    try:
                        # 画面にボタンがあるか
                        location = pyautogui.locateOnScreen(self.button_imgs["write"], confidence=0.9)
                        pyautogui.click(self.button_imgs["write"])
                    except pyautogui.ImageNotFoundException:
                        print('ImageNotFoundException: image not found') 
            try:
                # 合成結果をファイルに保存する
                win32gui.EnumWindows(write_emulate, "A.I.VOICE2")
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
        def play_emulate(hwnd, title):
            name = win32gui.GetWindowText(hwnd)
            if name.find(title) >= 0:
                hwnd = win32gui.FindWindow(None, name)
                win32gui.SetForegroundWindow(hwnd)
                # まだ再生中ならそれを停止
                if self._exist_image(self.button_imgs["stop"]):
                    self._click_image(self.button_imgs["stop"])
                count = 0
                while not self._exist_image(self.button_imgs["play"]):
                    count += 1
                    if count >= 5:
                        raise pyautogui.ImageNotFoundException()
                    time.sleep(1)
                # 音声再生
                self._click_image(self.button_imgs["play"])
                time.sleep(0.1)
                while True:
                    if self._exist_image(self.button_imgs["stop"]):
                        time.sleep(0.1)
                        continue
                    if self._exist_image(self.button_imgs["sentence_next"]):
                        self._click_image(self.button_imgs["sentence_next"])
                        self._click_image(self.button_imgs["play"])
                    else:
                        break
        win32gui.EnumWindows(play_emulate, "A.I.VOICE2")
        
    def _click_image(self, image_path):
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            x = math.floor(location.left + location.width / 2)
            y = math.floor(location.top + location.height / 2)
            pyautogui.click(x, y)
        except pyautogui.ImageNotFoundException:
            print(f"ImageNotFoundException: {image_path} image not found")
    
    def _exist_image(self, image_path):
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
        except pyautogui.ImageNotFoundException:
            return False
        return True
    
# aivoice2 = AIVoice2Talker(r"C:\Program Files\AI\AIVoice2\AIVoice2Editor\aivoice.exe")
# aivoice2.launch()
# aivoice2.speak("")