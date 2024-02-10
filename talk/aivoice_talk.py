import pythonnet
import clr
import os
import threading
from talk.talker import Talker
from datetime import datetime
import re
import json
import time

# このファイル内でのみ使用される
class aivoiceEditor():
    def __init__(self, aivoice_path : str) -> None:
        _editor_dir = aivoice_path

        if not os.path.isfile(_editor_dir + 'AI.Talk.Editor.Api.dll'):
            print("A.I.VOICE Editor (v1.3.0以降) がインストールされていません。")
            return

        # pythonnet DLLの読み込み
        clr.AddReference(_editor_dir + "AI.Talk.Editor.Api")
        from AI.Talk.Editor.Api import TtsControl, HostStatus

        self.tts_control = TtsControl()
        self.host_status = HostStatus

        # A.I.VOICE Editor APIの初期化
        host_name = self.tts_control.GetAvailableHostNames()[0]
        self.tts_control.Initialize(host_name)

        # A.I.VOICE Editorの起動
        if self.tts_control.Status == HostStatus.NotRunning:
            self.tts_control.StartHost()

class AIVoiceTalk(Talker):
    def __init__(self, aivoice_path : str) -> None:
        super().__init__()
        self._editor_dir = aivoice_path

    def exist(self) -> bool:
        if not os.path.isfile(self._editor_dir + 'AI.Talk.Editor.Api.dll'):
            print("A.I.VOICE Editorが見つかりませんでした")
            return False
        return True

    def initialize(self) -> aivoiceEditor:
        return aivoiceEditor(self._editor_dir)

    def launch(self) -> bool:
        th = threading.Thread(target=self.initialize)
        th.start()
        return self.exist()

    def speak(self, text : str, speaker : str | None = None, speaker_name = "noname", param_dict : dict | None = None, talk_flag : bool = True, voice_out_dir : str | None = None, write_flag : bool = False):
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
                aivoice.tts_control.SaveAudioToFile(f"{path}.wav")
                with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                    f.write(text)
                print(f"Voice save to {path}")
            except Exception as e:
                print(e)
        aivoice = aivoiceEditor(self._editor_dir)
        # 接続
        aivoice.tts_control.Connect()
        # ビジーか確認
        if aivoice.host_status.Busy == aivoice.tts_control.Status:
            aivoice.tts_control.Stop()
            time.sleep(1)
            
        if speaker is not None:
            # プリセット上書き
            aivoice.tts_control.CurrentVoicePresetName = speaker
        # テキスト設定
        aivoice.tts_control.Text = text
        aivoice.tts_control.TextSelectionStart = 0
        # マスターコントロールのパラメータ取得
        # JSON形式でVolume, Speed, Pitch, PitchRange, MiddlePause, LongPause, SentencePauseを実数値で指定 最小値最大値はエディター準拠 PitchRangeは抑揚
        master_param = aivoice.tts_control.MasterControl
        # 取得されるのは文字列なのでJSONとして変換
        master_param = json.loads(master_param)
        # キャラファイルの各項が空白でないときだけ上書き
        if param_dict is not None:
            if param_dict["volume"] != "":
                master_param["Volume"] = float(param_dict["volume"])
            if param_dict["speed"] != "":
                master_param["Speed"] = float(param_dict["speed"])
            if param_dict["pitch"] != "":
                master_param["Pitch"] = float(param_dict["pitch"])
            if param_dict["intonation"] != "":
                master_param["PitchRange"] = float(param_dict["intonation"])
            if param_dict["middle"] != "":
                master_param["MiddlePause"] = int(param_dict["middle"])
            if param_dict["long"] != "":
                master_param["LongPause"] = int(param_dict["long"])
            if param_dict["sentence"] != "":
                master_param["SentencePause"] = int(param_dict["sentence"])

        aivoice.tts_control.MasterControl = json.dumps(master_param)

        # ボイスプリセットのパラメータ取得
        voice_preset_param = aivoice.tts_control.GetVoicePreset(aivoice.tts_control.CurrentVoicePresetName)
        voice_preset_param = json.loads(voice_preset_param)
        if param_dict is not None and param_dict["presetFlag"].lower() == "true":
            # キャラファイルの各項が空白でないときだけ上書き
            param_names = {
                "presetVolume" : "Volume",
                "presetSpeed" : "Speed",
                "presetPitch" : "Pitch",
                "presetPitchRange" : "PitchRange",
            }
            for key, value in param_names.items():
                if param_dict[key] != "":
                    voice_preset_param[value] = float(param_dict[key])

            param_names = {
                "presetMiddlePause" : "MiddlePause",
                "presetLongPause" : "LongPause",
            }
            for key, value in param_names.items():
                if param_dict[key] != "":
                    voice_preset_param[value] = int(param_dict[key])

        aivoice.tts_control.SetVoicePreset(json.dumps(voice_preset_param))
        # print(master_param)
        # print(voice_preset_param)
        # パラメータ設定
        if write_flag and voice_out_dir is not None:
            save()
        # 再生
        if talk_flag:
            print(f"A.I.VOICE: {speaker_name} talking...")
            aivoice.tts_control.Play()
        # time.sleep((aivoice.tts_control.GetPlayTime() + 500) / 1000)
        # 切断
        aivoice.tts_control.Disconnect()