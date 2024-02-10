import other.Chatgpt as Chatgpt
from talk_type import TalkType

class Avatar():
    def __init__(self) -> None:
        self.system_prompt : str = ""
        self.avatar_name : str = "avatar"
        self.picture_path : str = ""
        self.picture_circle_path : str = ""
        self.talk_type : TalkType = TalkType.VOICEVOX
        self.talk_speaker : int = 0
        self.talk_speaker_uuid : str= ""
        self.pre_msg_list : list[dict[str, str]] = []
        self.chat_message_history : list = []

    def generate(self, text) -> str :
        chat = Chatgpt.Chatgpt()
        msg = chat.generate_gtp(self.system_prompt, text, self.pre_msg_list)
        self.pre_msg_list.append({"role" : "user", "content" : text})
        self.pre_msg_list.append({"role" : "assistant", "content" : msg})
        self.speak(msg)
        return msg
    
    def speak(self, text):
        pass

    def launch(self):
        pass