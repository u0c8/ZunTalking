import whisper
import speech_recognition as sr
from io import BytesIO
import numpy as np
import soundfile as sf

class SpeechWhisper:
    def __init__(self, model_str="base") -> None:
        self.recognizer = sr.Recognizer()
        self.model = whisper.load_model(model_str)

    def audio_to_text(file_path):
        model = whisper.load_model("base")
        result = model.transcribe(file_path, fp16=False, verbose=False)

        return result["text"]

    # 1回呼ぶごとにマイクから音声をテキスト変換して返す
    # ループ想定
    def speech_to_text(self) -> str | bool:
        # マイクから音声を取得
        with sr.Microphone(sample_rate=16_000) as source:
            print("なにか話してください")
            audio = self.recognizer.listen(source)

        print("音声処理中 ...")
        # 音声データをWhisperの入力形式に変換
        wav_bytes = audio.get_wav_data()
        wav_stream = BytesIO(wav_bytes)
        audio_array, sampling_rate = sf.read(wav_stream)
        audio_fp32 = audio_array.astype(np.float32)

        result = self.model.transcribe(audio_fp32, fp16=False, language="ja")
        print(result)
        ret_var = result["text"]
        if ret_var == "#認識できませんでした":
            ret_var = False
        return ret_var
    
# whisperText = SpeechText(model_str="small")
# for i in range(5):
#     tmp = whisperText.speech_to_text()
#     print(tmp)