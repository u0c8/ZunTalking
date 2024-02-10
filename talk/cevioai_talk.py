import configparser
import clr
import os
import threading
from talk.talker import Talker
from other.process_find import now_ps_find

class CeVIOAIEditor():
    def __init__(self, cevioai_path) -> None:
        self.cevioai_path = cevioai_path
        # pythonnet DLLの読み込み
        clr.AddReference(cevioai_path + "CeVIO.Talk.RemoteService2.dll")
        import CeVIO.Talk.RemoteService2

        # // 【CeVIO AI】起動
        # 起動されてない時だけ
        if not now_ps_find("cevio ai"):
            CeVIO.Talk.RemoteService2.ServiceControl2.StartHost(False)

        # // Talkerインスタンス生成
        self.talker = CeVIO.Talk.RemoteService2.Talker2()

        # // （例）音量設定
        # self.talker.Volume = 100

        # // （例）抑揚設定
        # self.talker.ToneScale = 100

class CeVIOAITalk(Talker):
    def __init__(self, cevioai_path) -> None:
        super().__init__()
        self.cevioai_path = cevioai_path
        self.cevioai = CeVIOAIEditor()

    def exist(self) -> bool:
        if os.path.exists(self.cevioai_path + "CeVIO.Talk.RemoteService2.dll"):
            return True
        return False

    def initialize(self):
        try:
            CeVIOAIEditor(self.cevioai_path)
        except Exception as e:
            print(e.__cause__)

    def launch(self) -> bool:
        self.initialize()
        for _ in range(10):
            if self.exist():
                return True
        return False

    def speak(self, text : str, speaker : str | None = None, speaker_name = "noname", param_dict : dict | None = None, voice_out_dir : str | None = None, write_flag : bool = False):
        def save():
            self.cevioai.talker.OutputWaveToFile(text, voice_out_dir)
        # キャスト設定
        if speaker is not None:
            self.cevioai.talker.Cast = speaker
        if param_dict is not None:
            if param_dict["volume"] != "":
                self.cevioai.talker.Volume = int(param_dict["volume"])
            if param_dict["speed"] != "":
                self.cevioai.talker.Speed = int(param_dict["speed"])
            if param_dict["pitch"] != "":
                self.cevioai.talker.Tone = int(param_dict["pitch"])
            if param_dict["intonation"] != "":
                self.cevioai.talker.ToneScale = int(param_dict["intonation"])
        
        if write_flag  and voice_out_dir is not None:
            save()
        # 再生
        state = self.cevioai.talker.Speak(text)