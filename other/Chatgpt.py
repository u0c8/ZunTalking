# openaiライブラリの刷新に合わせて大幅に書き直し
from openai import OpenAI
import API_file
import other.const as const
import other.weather as weather
from names import Confignames
import configparser
from pprint import pprint

const.OPENAI_API_KEY = API_file.openaiLoad()

class Chatgpt:
    output = None
    def __init__(self):
        self.client = OpenAI(
            api_key=const.OPENAI_API_KEY
        )
        self.output = ""
        self.useable_gtp4 = not API_file.is_default()
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, "utf-8")
        # 使用モデルの決定
        models = {"gpt-3.5" : "gpt-3.5-turbo", "gpt-4" : "gpt-4"}
        if self.useable_gtp4:
            self.model = models[config["USER"]["GPTmodel"]]
        else:
            self.model = models["gpt-3.5"]
        print(f"{self.model} calling...")
    
    def generate_gtp(self, system_prompt : str, text : str, pre_msg_list : list[dict[str, str]]):
        # ChatGPTにプロンプトを渡す
        # 特定条件を満たすとき、システムプロンプトを追加する
        subsystem_prompt = ""
        if text.find("天気") != -1:
            # 会話ワードに「天気」があるとき、現在の天気をシステムプロンプトとして与える
            weather_dict = weather.weather_call_google()
            subsystem_prompt += "現在の" + weather_dict["location"] + "の気温は" + weather_dict["temp"] + "、天気は" + weather_dict["weather"] + "です。\n天気について聞かれたときは詳細に答えてください。"
        prompt = [
            {"role": "system", "content": system_prompt + subsystem_prompt},
        ]
        prompt.extend(pre_msg_list)
        prompt.append({"role": "user", "content": text})
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
        )

        # pprint(completion)
        msg = completion.choices[0].message.content
        # print(msg)
        return msg