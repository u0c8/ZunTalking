import os
import configparser
import requests
from bs4 import BeautifulSoup
from names import Confignames

# 設定ファイルの地名で天気を検索
def weather_call_google(query="天気") -> dict[str,str]:
  config = configparser.ConfigParser()
  config.read(Confignames.SETTING, "UTF-8")
  location = config["USER"]["location"]
  return weather_call_google_location(location, query)

# 特定の地点を指定して天気を検索
def weather_call_google_location(location :str, query="天気") -> dict[str, str]:
  weather_dict : {str,str} = {}

  url = "https://www.google.com/search?q=" + query + location
  response = requests.get(url)
  # file = open("google.html", "w", encoding="UTF-8")
  # file.write(response.text)
  soup = BeautifulSoup(response.text, "html.parser")
  elems = soup.select(".BNeawe.iBp4i.AP7Wnd")
  try:
    weather_dict["temp"] = elems[1].contents[0] # 気温

    elems = soup.select(".BNeawe.tAd8D.AP7Wnd")
    weather_dict["location"] = elems[0].contents[0] # 地区

    tmp_list = str(elems[2].contents[0]).split("\n")
    weather_dict["time"] = tmp_list[0].split(" ")[1] # 時間
    weather_dict["weather"] = tmp_list[1] # 天気
  except Exception as e:
    print("エラー　天気検索Googleにて　要素が取得できない")
    print(e.__str__())
    weather_dict["temp"] = "-265K"
    weather_dict["location"] = "??"
    weather_dict["time"] = "00:00"
    weather_dict["weather"] = "晴"
  return weather_dict


def weather_type_icon() -> dict[str,str]:
  return {
    "icons_folder" : f"{os.sep}WeatherIconPack_png{os.sep}Icons{os.sep}",
    "晴" : "100.png",
    "晴時々曇" : "101.png",
    "晴一時雨" : "102.png",
    "晴一時雪" : "104.png",
    "晴のち曇" : "110.png",
    "曇" : "200.png",
    "曇時々晴" : "201.png",
    "曇のち晴" : "210.png",
    "雨" : "300.png",
    "雪" : "400.png",
    "雪時々晴" : "401.png",
    "雪時々雨" : "403.png",
    "雪のち晴" : "411.png",
  }

def weather_to_icon(weather : str) -> str:
  weather_type_dict = weather_type_icon()
  icon = weather_type_dict["icons_folder"]
  try:
    icon += weather_type_dict[weather]
  except KeyError:
    if weather.find("晴") != -1:
      icon += weather_type_dict["晴"]
    elif weather.find("曇") != -1:
      icon += weather_type_dict["曇"]
    elif weather.find("雨") != -1:
      icon += weather_type_dict["雨"]
    elif weather.find("雪") != -1:
      icon += weather_type_dict["雪"]
    else:
      raise KeyError(f"不明な天気名: {weather}")
  return icon