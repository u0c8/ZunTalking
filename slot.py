from avatar import Avatar
from talk_type import TalkType
import configparser
from talk.talker import Talker, AIVoice2Talker
from talk.voicevox_talk import VoicevoxTalk
from talk.aivoice_talk import AIVoiceTalk
from talk.coeiroink_talk import CoeiroinkTalk
from talk.aques_talk import AquesTalk
from talk.cevioai_talk import CeVIOAITalk
import threading
import time
import flet as ft
from other.process_find import now_ps_find
from configcontrol import ConfigController
import os

class Slot(Avatar):
    def __init__(self, slot_file_name : str) -> None:
        super().__init__()
        def ini_read_none(parser: configparser.ConfigParser, section: str, key: str):
            try:
                return parser[section][key]
            except KeyError as e:
                return None
        slot = configparser.ConfigParser()
        slot.read(slot_file_name, "UTF-8")
        CHARA = "CHARA"
        IMAGE = "IMAGE"
        self.avatar_name = ini_read_none(slot, CHARA, "name")
        self.system_prompt = ini_read_none(slot, CHARA, "persona")
        self.picture_path = slot[IMAGE]["picture_path"]
        eye_blind_flag = ini_read_none(slot, IMAGE, "eye_blind_flag")
        self.eye_blind_flag = eye_blind_flag.lower() == "true" if eye_blind_flag is not None else None
        self.eye_blind_open = ini_read_none(slot, IMAGE, "eye_blind_open")
        self.eye_blind_little_close = ini_read_none(slot, IMAGE, "eye_blind_little_close")
        self.eye_blind_half_close = ini_read_none(slot, IMAGE, "eye_blind_half_close")
        self.eye_blind_largely_close = ini_read_none(slot, IMAGE, "eye_blind_largely_close")
        self.eye_blind_close = ini_read_none(slot, IMAGE, "eye_blind_close")
        lip_sync_flag = ini_read_none(slot, IMAGE, "lip_sync_flag")
        self.lip_sync_flag = lip_sync_flag.lower() == "true" if lip_sync_flag is not None else None
        self.picture_circle_path = slot[IMAGE]["picture_circle_path"]
        self.talk_flag = slot["VOICE"]["talk_flag"].lower() == "true"
        configc = ConfigController()
        self.voice_save_flag = configc.read("writeVoice").lower() == "True".lower()
        self.talk_type = None
        self.talk_speaker = None
        self.talk_speaker_uuid = None
        self.talk_param = None
        if self.talk_flag:
            self.talk_type = slot["VOICE"]["talk_type"]
            self.talk_speaker = slot["VOICE"]["talk_speaker"]
            self.talk_speaker_uuid = slot["VOICE"]["talk_speaker_uuid"]
            self.talk_param = {
                "speed" : slot["PARAM"]["speedScale"],
                "pitch" : slot["PARAM"]["pitchScale"],
                "intonation" : slot["PARAM"]["intonationScale"],
                "volume" : slot["PARAM"]["volumeScale"],
                "prePhoneme" : slot["PARAM"]["prePhonemeLength"],
                "postPhoneme" : slot["PARAM"]["postPhonemeLength"],
                "middle" : slot["AIVOICEPARAM"]["middlePause"],
                "long" : slot["AIVOICEPARAM"]["longPause"],
                "sentence" : slot["AIVOICEPARAM"]["sentencePause"],
                "presetFlag" : slot["AIVOICEPARAM"]["presetFlag"],
                "presetVolume" : slot["AIVOICEPARAM"]["presetVolume"],
                "presetSpeed" : slot["AIVOICEPARAM"]["presetSpeed"],
                "presetPitch" : slot["AIVOICEPARAM"]["presetPitch"],
                "presetPitchRange" : slot["AIVOICEPARAM"]["presetPitchRange"],
                "presetMiddlePause" : slot["AIVOICEPARAM"]["presetMiddlePause"],
                "presetLongPause" : slot["AIVOICEPARAM"]["presetLongPause"],
            }
            configc = ConfigController()
            self.talker = None
            self.psname = ""
            match self.talk_type:
                case TalkType.VOICEVOX:
                    self.talker = VoicevoxTalk(configc.read("voicevoxPath", "VOICEVOX"))
                    self.psname = "voicevox"
                case TalkType.AIVOICE:
                    self.talker = AIVoiceTalk(configc.read("aivoiceEditorPath"))
                    self.psname = "aivoice"
                case TalkType.AIVOICE2:
                    self.talker = AIVoice2Talker(configc.read("aivoice2Path"))
                    self.psname = "AIVoice2"
                case TalkType.COEIROINK:
                    self.talker = CoeiroinkTalk(configc.read("coeiroinkPath"))
                    self.psname = "coeiroink"
                case TalkType.AQUESTALK:
                    self.talker = AquesTalk(configc.read("aquestalkPath"))
                    self.psname = "aquestalk"
                case TalkType.CEVIOAI:
                    self.talker = CeVIOAITalk(configc.read("cevioaiPath"))
                    self.psname = "cevio ai"

    def launch(self):
        # 現在のプロセス一覧から対象ソフトが起動済みかチェック
        if now_ps_find(self.psname):
            # print(self.psname)
            return None
        # まだ起動していないので立ち上げ
        if self.talker.launch():
            print(f"Launching {self.talk_type}")
            return None
        # 上2つが失敗
        return self.launch_failed()

    def launch_failed(self) -> ft.AlertDialog:
        alert = ft.AlertDialog(title=ft.Text(self.talk_type + "は見つかりませんでした"), content=ft.Text("これはクラッシュを引き起こす可能性があります"))
        return alert

    def speak(self, text):
        configc = ConfigController()
        voice_out_dir = os.path.dirname(configc.read("voiceOutputDirectory")) # 出力先
        if self.talk_type == TalkType.VOICEVOX:
            voicevox = VoicevoxTalk(configc.read("voicevoxPath", "VOICEVOX"))
            voicevox_framerate = int(configc.read("framerate", "VOICEVOX"))
            thread = threading.Thread(target=voicevox.speak, args=[text, self.talk_speaker, self.avatar_name, voicevox_framerate, self.talk_param], kwargs={"talk_flag": self.talk_flag,"voice_out_dir" : voice_out_dir, "write_flag" : self.voice_save_flag})
            thread.start()
            time.sleep(1)
        elif self.talk_type == TalkType.AIVOICE:
            aivoice = AIVoiceTalk(configc.read("aivoiceEditorPath"))
            aivoice.speak(text, self.talk_speaker, speaker_name=self.avatar_name, voice_out_dir=voice_out_dir, write_flag=self.voice_save_flag, param_dict=self.talk_param, talk_flag=self.talk_flag)
        elif self.talk_type == TalkType.AIVOICE2:
            self.talker.speak(text, voice_out_dir=voice_out_dir, write_flag=self.voice_save_flag)
        elif self.talk_type == TalkType.COEIROINK:
            thread = threading.Thread(target=self.talker.speak, args=[text, self.talk_speaker, self.talk_speaker_uuid, self.avatar_name, int(configc.read("framerate", "COEIROINK")), self.talk_param], kwargs={"talk_flag" : self.talk_flag, "voice_out_dir" : voice_out_dir, "write_flag" : self.voice_save_flag})
            thread.start()
            time.sleep(1)
        elif self.talk_type == TalkType.AQUESTALK:
            # aquestalk = AquesTalk(configc.read("aquestalkPath"))
            self.talker.speak(text, self.talk_speaker, speaker_name=self.avatar_name, talk_flag=self.talk_flag,voice_out_dir=voice_out_dir, write_flag=self.voice_save_flag)
        elif self.talk_type == TalkType.CEVIOAI:
            CeVIOAITalk.speak(text, self.talk_speaker)