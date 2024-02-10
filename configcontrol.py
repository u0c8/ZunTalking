from names import Confignames
import os
import configparser

# このクラスを使ってsetting.iniを読み書きする場合、キー名は小文字と大文字を区別する
class ConfigController:
    def __init__(self) -> None:
        self.config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        self.config.optionxform = str
        self.reload()

    def reload(self):
        self.config.read(Confignames.SETTING, encoding="UTF-8")

    def write_file(self):
        with open(Confignames.SETTING, encoding="UTF-8", mode="w") as file:
            self.config.write(file)

    def get(self):
        return self.config
    
    def read(self, key, section = "USER"):
        return self.config[section][key]
    
    def write(self, key, value, section = "USER"):
        self.config[section][key] = value