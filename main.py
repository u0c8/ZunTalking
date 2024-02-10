from pprint import pprint
import sys
import flet as ft
import controls.message as message
import configparser
import datetime
from names import Confignames
import os
from shutil import rmtree
import subprocess
import threading
from configcontrol import ConfigController
from control import RouteView, SettingView, WeatherView, AvatarView

def main(page: ft.Page):
    tmp_dir = f"tmp"
    if os.path.isdir(tmp_dir):
        rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    try:
        out_file = open(r"stdout.txt", "a", encoding="UTF-8")
    except OSError as e:
        # 予期しないエラーキャッチ
        print(e)
    try:
        error_file = open(r"stderr.txt", "a", encoding="UTF-8")
    except OSError as e:
        # 予期しないエラーキャッチ
        print(e)
    sys.stdout = out_file
    sys.stderr = error_file
    print(datetime.datetime.now())

    # ホストを指定します（pingを送信したい対象のIPアドレスまたはホスト名）
    host = "www.google.com"
    is_online = False

    # pingコマンドを実行
    try:
        result = subprocess.run(["ping",  '-n', '1', host], stdout=subprocess.PIPE, text=True, check=True)
        print(result.stdout)
        print(f"{host}へのpingが通りました")
        is_online = True
    except subprocess.CalledProcessError as e:
        print(f"pingコマンドがエラーを返しました: {e}")
    except FileNotFoundError:
        print("pingコマンドが見つかりませんでした。")
    
    # page.window_title_bar_hidden = True
    page.window_width = 900
    page.window_height = 590
    page.window_min_width = 800
    page.window_min_height = 400
    # page.window_resizable = False
    # page.window_maximizable = False
    page.theme = ft.Theme(color_scheme_seed="green")
    page.dark_theme = ft.Theme(color_scheme_seed="green")
    # page.bgcolor = ft.colors.WHITE

    config = configparser.ConfigParser()
    config.read(Confignames.SETTING, encoding="UTF-8")
    if config["USER"]["theme"] == "SYSTEM":
        page.theme_mode = ft.ThemeMode.SYSTEM
    elif config["USER"]["theme"] == "LIGHT":
        page.theme_mode = ft.ThemeMode.LIGHT
    elif config["USER"]["theme"] == "DARK":
        page.theme_mode = ft.ThemeMode.DARK
    else:
        print("setting.iniのテーマ設定が規定値以外")
    page.update()

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.title = "ずんとーきん！"

    # View
    view_dict = {
        "/" : RouteView(page),
        "/weather" : RouteView(page),
        "/avatar" : AvatarView(page),
        "/setting" : SettingView(page),
    }
    if is_online:
        view_dict["/weather"] = WeatherView(page)

    def resize(e):
        width = page.window_width
        height = page.window_height
        view_dict["/"].resize(width, height)
        view_dict["/weather"].resize(width, height)
        view_dict["/avatar"].resize(width, height)
        view_dict["/setting"].resize(width, height)
        page.update()

    def route_change(route):
        # print("route change")
        page.views.clear()
        # [view.reload() for view in view_dict.values()]
        # if page.route == "/":
        page.views.append(view_dict["/"])
        if page.route == "/weather":
            page.views.append(view_dict["/weather"])
        if page.route == "/avatar":
            page.views.append(view_dict["/avatar"])
        if page.route == "/setting":
            page.views.append(view_dict["/setting"])
        page.update()
    
    def on_message(message : message.Message):
        view_dict["/"].on_message(message)

    def view_pop(view):
        page.views.pop()
        page.go("/")

    page.on_resize = resize
    page.on_view_pop = view_pop
    page.pubsub.subscribe(on_message)
    page.on_route_change = route_change
    # pageの初期化
    page.go(page.route)
    resize(0)

# tmpフォルダがないとき、作成する
if(not os.path.isdir("tmp")):
    os.mkdir("tmp")
    
ft.app(target=main, assets_dir="assets")