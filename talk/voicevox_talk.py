import requests
import subprocess
import simpleaudio
import os
from talk.talker import Talker
from datetime import datetime
import re

class VoicevoxTalk(Talker):
    def __init__(self, voicevox_path) -> None:
        super().__init__()
        self.voicevox_path = voicevox_path

    def exist(self) -> bool:
        if not os.path.isfile(self.voicevox_path):
            print("VOICEVOXが見つかりませんでした")
            return False
        return True

    def launch(self) -> bool:
        # VoicevoxTalk.speakers()
        if not self.exist():
            return False
        try:
            boot = requests.get("http://127.0.0.1:50021/version")
        except requests.exceptions.ConnectionError:
            subprocess.Popen(self.voicevox_path)
        return True

    def speak(self, text : str, speaker : int, speaker_name = "noname", framerate = 24000, param_dict : dict | None = None, talk_flag : bool = True, voice_out_dir : str | None = None, write_flag : bool = False):
        def save(wave_data):
            # パス整形
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            sliced_text = text[:10]
            sliced_text = re.sub(r'[\\/:*?"<>|]+', '' , sliced_text)
            path = f"{voice_out_dir}\\{timestamp}_{speaker_name}_{sliced_text}"
            # 保存
            try:
                wr = open(f"{path}.wav", "wb")
                wr.write(wave_data)
                wr.close()
                # with wave.open(f"{path}.wav", "wb") as f:
                #     f.setnchannels(2)   # チャンネル数
                #     f.setframerate(framerate)   # サンプリングレート
                #     f.setsampwidth(1)
                #     f.close()
                with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                    f.write(text)
                print(f"Voice save to {path}")
            except Exception as e:
                print(e)
        # もしVOICEVOXが見つからないなら処理終了
        if not self.exist():
            return
        response = None
        count = 0
        while response is None or count < 5:
            try:
                response : requests.Response = requests.post(f"http://127.0.0.1:50021/audio_query?text={text}&speaker={speaker}")
            except requests.ConnectionError as e:
                self.launch()
            count += 1
        response_dict = response.json()
        if param_dict["speed"] != "":
            response_dict["speedScale"] = param_dict["speed"]
        if param_dict["pitch"] != "":
            response_dict["pitchScale"] = param_dict["pitch"]
        if param_dict["intonation"] != "":
            response_dict["intonationScale"] = param_dict["intonation"]
        if param_dict["volume"] != "":
            response_dict["volumeScale"] = param_dict["volume"]
        if param_dict["prePhoneme"] != "":
            response_dict["prePhonemeLength"] = param_dict["prePhoneme"]
        if param_dict["postPhoneme"] != "":
            response_dict["postPhonemeLength"] = param_dict["postPhoneme"]
        # response_dict["outputStereo"] = param_dict["stereo"]
        response_dict["outputSamplingRate"] = framerate
        resp_wav : requests.Response = requests.post(f"http://127.0.0.1:50021/synthesis?speaker={speaker}", json=response_dict)
        data_binary : bytes = resp_wav.content
        # 音声を書き出すか？
        if write_flag and voice_out_dir is not None:
            save(data_binary)
        # 今しゃべるか？
        if talk_flag:
            wav_obj = simpleaudio.WaveObject(data_binary, 1, 2, framerate)
            print(f"VOICEVOX: {speaker_name} talking...")
            wav_obj.play()

    def speakers_write():
        response = requests.get("http://127.0.0.1:50021/speakers")
        # with open("voicevoxspeakers.json", "w", encoding="UTF-8") as f:
        #     json.dump(response.json(), f, ensure_ascii=False, indent=4)
        json_dict = response.json()
        lines = []
        for d in json_dict:
            line = [d["name"], d["styles"]]
            lines.append(line)
        with open("voicevox_speakers.txt", "w", encoding="UTF-8") as f:
            for line in lines:
                for l in line:
                    f.write(str(l))
                f.write("\n")