import sys
import flet as ft
import os
import math
import datetime
import configparser
from talk_type import TalkType
import requests
from configcontrol import ConfigController
from component.navigation import MenuNavi
from component.titlebar import WindowTitleBar, WindowAppBar
from component.activate_avatar_row import ActivateAvatarRow
from other import weather, prefecture
from controls.message import Message, ChatMessage
from avatar import Avatar
from slot import Slot
import other.SpeechRecognizer as SpeechRecognizer
from names import Confignames, DataPath
import playsound

class RouteView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.APPBAR_HEIGHT = 50
        # ユーザアバターを読み込む
        configc = ConfigController()
        user_avatar_path = configc.read("userAvatarPath")
        if user_avatar_path is None or user_avatar_path == "":
            user_avatar_path = f".{os.sep}avatar{os.sep}user.chr"
        self.user_avatar = Slot(user_avatar_path)
        user_voice_play_enable = configc.read("userVoicePlay").lower() == "true"
        user_voice_save_enable = configc.read("userVoiceSave").lower() == "true"
        self.user_avatar.talk_flag = user_voice_play_enable
        self.user_avatar.voice_save_flag = user_voice_save_enable
        self.avatar_list = []
        self.now_avatar_index = 0
        self.now_avatar : Avatar = None
        # アバターロードは別関数
        self.load_avatars()

        # SpeechRecognizerを起動しておく
        try:
            self.speech = SpeechRecognizer.SpeechRecognizer()
        except Exception as e:
            # マイクがないとエラーになる？
            print(e)
            
        # コントロール宣言
        # メニューボタン
        pb_menu = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(icon=ft.icons.SEND_ROUNDED, text="あなたのことを教えて！", on_click=self.quick_message),
                ft.PopupMenuItem(icon=ft.icons.SEND_ROUNDED, text="今日の天気は？", on_click=self.quick_message),
                ft.PopupMenuItem(icon=ft.icons.CACHED, text="アバターを再読み込み", on_click=lambda _: self.reload()),
            ],
            tooltip="各種設定",
        )
        appbar : ft.AppBar = ft.AppBar(
            title=ft.Text("メイン画面"), 
            bgcolor=ft.colors.SURFACE_VARIANT,
            toolbar_height=self.APPBAR_HEIGHT,
            leading=pb_menu,
        )

        # メニューエリア(left)
        # メニューコンテナ
        self.ct_menu = MenuNavi(page)

        # チャットエリア(Center)
        # チャットリストビュー
        self.lv_chat : ft.ListView = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
        )
        # チャット入力ボックス
        self.tf_chat : ft.TextField = ft.TextField(
            label="チャットを送信",
            hint_text="1文以上の文章",
            autofocus=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
            bgcolor=ft.colors.GREEN_50,
            # focused_bgcolor=ft.colors.GREEN_100,
            expand=True,
            on_submit=lambda _: self.send_message_click(),
        )
        # チャットカラム コンテナを縦2段に積む
        self.cl_chat : ft.Column = ft.Column(
            controls=[
                # チャットコンテナ(Center,top)
                ft.Container(
                    content=self.lv_chat,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    expand=True,
                    padding=10,
                ),
                # 入力コンテナ(Center,bottom)
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.MIC_NONE_SHARP,
                                tooltip="マイクで会話モード　トグル : オフ\n調整中",
                                on_click=lambda e: self.onclick_mic(e),
                                selected_icon=ft.icons.MIC_SHARP,
                                selected=False,
                                icon_color="#373735",
                                bgcolor="#93e090",
                            ),
                            ft.IconButton(
                                icon=ft.icons.CLEANING_SERVICES_SHARP,
                                tooltip="選択中のキャラの会話履歴を消去",
                                on_click=lambda _: self.cleanup_message(),
                                icon_color="#373735",
                                bgcolor="#93e090",
                            ),
                            self.tf_chat,
                            ft.IconButton(
                                icon=ft.icons.SEND_ROUNDED,
                                tooltip="送信ボタン(Enter)",
                                on_click= lambda _: self.send_message_click(),
                                icon_color="#373735",
                                bgcolor="#93e090",
                            ),
                        ]
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            width=200,
        )

        # 立ち絵表示エリア(right)
        # Imageコントロール
        self.img_chara = ft.Image(
            src=self.now_avatar.picture_path,
            # fit=ft.ImageFit.CONTAIN
        )
        ct_img_chara = ft.Container(
            content=self.img_chara,
            expand=True,
        )
        row_chara = ft.Row(
            controls=[
                ft.IconButton(icon=ft.icons.KEYBOARD_ARROW_LEFT, icon_size=30, tooltip="前のキャラクター", on_click=lambda _: self.change_avatar((self.now_avatar_index + len(self.avatar_list) - 1) % len(self.avatar_list))),
                ft.Text(self.now_avatar.avatar_name, size=20),
                ft.IconButton(icon=ft.icons.KEYBOARD_ARROW_RIGHT, icon_size=30, tooltip="次のキャラクター", on_click=lambda _: self.change_avatar((self.now_avatar_index + 1) % len(self.avatar_list))),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        # 立ち絵カラム
        cl_chara = ft.Column(
            controls=[
                ct_img_chara,
                row_chara,
            ],
        )
        # 立ち絵コンテナ
        self.ct_chara : ft.Container = ft.Container(
            content=cl_chara,
            # col=4,
            width=200,
            alignment=ft.alignment.top_right,
        )

        self.route = "/"
        self.appbar = appbar
        self.controls = [
            # WindowTitleBar(title="チャット - ずんとーきん！", page=self.page),
            ft.Row(
                controls=[
                    self.ct_menu,
                    self.cl_chat,
                    self.ct_chara,
                ],
                spacing=20,
                expand=True,
            ),
        ]
        self.page.update()
        # init終了
        
    # イベントハンドラ関数宣言
    def send_message_click(self) :
        if self.tf_chat.value != "" :
            self.page.pubsub.send_all(Message(self.user_avatar, "User", self.tf_chat.value, message_type="chat_user"))
            self.tf_chat.value = ""
            # self.tf_chat.focus()
            self.page.update()

    def on_message(self, message : Message):
        def call_timesignal() -> str:
            now = datetime.datetime.now()
            now_hour = now.hour
            path = DataPath.TIME_VOICES + f"\時報" + str(now_hour) + "時.wav"
            playsound.playsound(path)
            # wav_obj = simpleaudio.WaveObject.from_wave_file(path)
            # play_obj = wav_obj.play()
            return "現在時刻はだいたい" + str(now_hour) + "時くらいです"
        
        def call_soundtest() -> str:
            path = DataPath.TIME_VOICES + f"\音声テスト.mp3"
            playsound.playsound(path)
            return "音声テスト.mp3を再生します"

        one_command_func = {"時報" : call_timesignal, "テスト" : call_soundtest, "test" : call_soundtest}
        one_command_func = {}
        if message.message_type == "chat_user":
            m = ChatMessage(message)
            self.lv_chat.controls.append(m)
            self.lv_chat.update()
            text = message.text
            # ユーザのボイスを再生・保存
            self.user_avatar.speak(text)
            msg = ""
            if text in one_command_func.keys():
                try:
                    msg = one_command_func[text]()
                except Exception as e:
                    print(e)
                    alert = ft.AlertDialog(title=ft.Text("シングルコマンドでエラー"), content=ft.Text("ファイル参照がおかしいかもしれません。"))
                    self.page.dialog = alert
                    alert.open = True
                    msg = "このメッセージが 見えるのは おかしいよ"
            else:
                try:
                    msg = self.now_avatar.generate(text)
                except Exception as e:
                    print(e.args)
                    alert = ft.AlertDialog(title=ft.Text("テキスト生成が失敗"), content=ft.Text("APIの呼び出しか音声合成で失敗しました。\nAPIキーの設定を見直してみてください。\nインターネット接続を見直してみてください。"))
                    self.page.dialog = alert
                    alert.open = True
                    msg = "このメッセージが 見えるのは おかしいよ"
            gptm = ChatMessage(Message(self.now_avatar, self.now_avatar.avatar_name, msg, message_type="chat_gpt"))
            self.lv_chat.controls.append(gptm)
        self.page.update()

    def quick_message(self, e):
        msg = e.control.text
        self.page.pubsub.send_all(Message(self.user_avatar, "User", msg, message_type="chat_user"))
        self.page.update()

    def cleanup_message(self):
        self.now_avatar.pre_msg_list.clear()
        self.lv_chat.controls.clear()
        # スナックバーの表示
        self.page.snack_bar = ft.SnackBar(ft.Text(f"{self.now_avatar.avatar_name}の会話履歴を削除しました。"))
        self.page.snack_bar.open = True
        self.page.update()

    def onclick_mic(self, e : ft.ControlEvent):
        if e.control.selected:
            # すでにマイクが起動状態である
            e.control.selected = False
            e.control.tooltip = "マイクで会話モード　トグル : オフ\n※仮実装"
            self.page.update()
            print("マイクオフ")
        else:
            # マイクを起動する
            e.control.selected = True
            e.control.tooltip = "マイクで会話モード　トグル : オン\n※仮実装"
            self.page.update()
            while e.control.selected:
                sp_text = self.speech.speech_to_text()
                if sp_text != "" and sp_text != False:
                    self.page.pubsub.send_all(Message(self.user_avatar, "User", sp_text, message_type="chat_user"))
            print("音声認識終了")

    # ウィンドウの幅と高さを与えてコントロールの値を調整
    # 非常に低速
    def resize(self, window_width : int, window_height : int) -> None :
        # ナビゲーションの分補正
        correct_width = window_width - 80
        self.cl_chat.width = math.floor(correct_width * 0.6)
        self.ct_chara.width = math.floor(correct_width * 0.3)
        # AppBarの部分を補正
        correction_height : int = window_height - (self.APPBAR_HEIGHT + 12)
        self.ct_menu.height = correction_height
        self.cl_chat.height = correction_height
        self.ct_chara.height = correction_height

    def reload(self):
        self.lv_chat.controls.clear()
        self.lv_chat.update()
        configc = ConfigController()
        user_voice_play_enable = configc.read("userVoicePlay").lower() == "true"
        user_voice_save_enable = configc.read("userVoiceSave").lower() == "true"
        self.user_avatar.talk_flag = user_voice_play_enable
        self.user_avatar.voice_save_flag = user_voice_save_enable
        self.load_avatars()
        self.change_avatar(self.now_avatar_index)
        self.page.update()

    def load_avatars(self):
        print("Loading all avatars")
        # アバターをすべて読み込みリストに保持
        avatars = configparser.ConfigParser()
        avatars.read(Confignames.AVATARS, "UTF-8")
        items = avatars.items("AVATAR")

        self.avatar_list = []
        self.now_avatar_index = int(avatars["OTHER"]["launch_id"])

        for item in items:
            try:
                self.avatar_list.append(Slot(item[1]))
            except KeyError as e:
                print(e)
                alert = ft.AlertDialog(title=ft.Text("指定されたアバターファイルが見つかりませんでした"), content=ft.Text(Confignames.AVATARS + "を確認してみてください。\n指定したファイル名が間違っている場合読み込まれません。"))
                self.page.dialog = alert
                alert.open = True
            except Exception as e:
                print(e)
                alert = ft.AlertDialog(title=ft.Text("不明なエラー"), content=ft.Text("原因不明のエラーです。ログファイルを開発者に報告すれば解決するかもしれません。"))
                self.page.dialog = alert
                alert.open = True
        # 現在のアバター設定のインデックス
        # self.now_avatar_index = int(avatars["OTHER"]["launch_id"])
        # 現在のアバター設定
        try:
            self.now_avatar : Avatar = self.avatar_list[self.now_avatar_index]
        except IndexError as e:
            print(e)
            alert = ft.AlertDialog(title=ft.Text("launch_idがキャラ数を超えています"), content=ft.Text(Confignames.AVATARS + "を確認してみてください。\n一般に、n番目のキャラを選ぶときはn-1を入力する必要があります。"))
            self.page.dialog = alert
            alert.open = True
            self.now_avatar = self.avatar_list[0]
        self.avatar_launch()

    def change_avatar(self, index : int):
        self.now_avatar.chat_message_history.clear()
        self.now_avatar.chat_message_history.extend(self.lv_chat.controls)
        self.lv_chat.controls.clear()
        self.now_avatar_index = index
        self.now_avatar = self.avatar_list[self.now_avatar_index]
        self.lv_chat.controls.extend(self.now_avatar.chat_message_history)
        self.img_chara.src = self.now_avatar.picture_path
        if not os.path.isfile(self.now_avatar.picture_path):
            self.img_chara.src = f"image\image.png"
            print(self.now_avatar.avatar_name + "の画像が見つかりませんでした")
        self.ct_chara.content.controls[1].controls[1].value = self.now_avatar.avatar_name
        self.avatar_launch()
        print(f"Change to {self.now_avatar.avatar_name} voice type {self.now_avatar.talk_type}")
        self.page.update()

    def avatar_launch(self):
        alert = self.now_avatar.launch()
        if alert is not None:
            self.page.dialog = alert
            alert.open = True
            self.page.update()

class SettingView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        # 関数定義
        # 設定　天気予報で使う関数
        def prefecture_change(e):
            now_selected = e.control.value
            detail_list = prefecture.get_prefecture_dict()[now_selected]
            option_list = []
            for value in detail_list:
                option_list.append(ft.dropdown.Option(value))
            dr_prefecture_detail.options = option_list
            self.page.update()
        # def prefecture_detail_change(e):
        #     now_selected = e.control.value
        #     config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        #     config.optionxform = str
        #     config.read(Confignames.SETTING, encoding="UTF-8")
        #     config["USER"]["location"] = now_selected
        #     with open(Confignames.SETTING, encoding="UTF-8", mode="w") as file:
        #         config.write(file)

        def save_setting(_):
            configc = ConfigController()
            # 編集した設定を変数に読み込む
            theme_selected = theme_dict[dr_theme.value]
            location_selected = dr_prefecture_detail.value
            aivoice_path = txf_aivoice.value
            voicevox_path = txf_voicevox.value
            coeriroink_path = txf_coeiroink.value
            aquestalk_path = txf_aquestalk.value
            voice_output_path = txf_voice.value
            write_voice_flag = sw_voice_save.value
            user_avatar_path = txf_user_avatar.value
            user_voice_play = sw_user_voice_play.value
            user_voice_save = sw_user_voice_save.value
            # テーマの適用
            theme_mode = {"SYSTEM" : ft.ThemeMode.SYSTEM, "LIGHT" : ft.ThemeMode.LIGHT, "DARK" : ft.ThemeMode.DARK}
            try:
                self.page.theme_mode = theme_mode[theme_selected]
            except Exception as e:
                print(e)
                print("テーマエラー")
            self.page.update()
            # 簡易バリデーションと書き込み
            if theme_selected != "":
                configc.write("theme", theme_selected)
            if location_selected != "":
                configc.write("location", location_selected)
            if aivoice_path != "":
                configc.write("aivoiceEditorPath", aivoice_path)
            if voicevox_path != "":
                configc.write("voicevoxPath", voicevox_path, section="VOICEVOX")
            if coeriroink_path != "":
                configc.write("coeiroinkPath", coeriroink_path)
            if aquestalk_path != "":
                configc.write("aquestalkPath", aquestalk_path)
            if voice_output_path != "":
                configc.write("voiceOutputDirectory", voice_output_path)
            if write_voice_flag != None:
                configc.write("writeVoice", str(write_voice_flag))
            if user_avatar_path != "":
                configc.write("userAvatarPath", user_avatar_path)
            if user_voice_play != None:
                configc.write("userVoicePlay", str(user_voice_play))
            if user_voice_save != None:
                configc.write("userVoiceSave", str(user_voice_save))
            # ファイルへ書き込み
            configc.write_file()

            # スナックバーの表示
            self.page.snack_bar = ft.SnackBar(ft.Text(f"設定を保存しました。"))
            self.page.snack_bar.open = True
            self.page.update()
        
        # 基本設定
        # フォントサイズ
        configc = ConfigController()
        font_size = int(configc.read("fontSize"))
        font_template = {
            "headline": font_size * 1.5,
            "body": font_size,
        }
        # テーマの変更
        theme_dict = {"ライト" : "LIGHT", "ダーク" : "DARK", "システム依存" : "SYSTEM"}
        theme_dict_swap = {v: k for k, v in theme_dict.items()}
        now_theme = configc.read("theme")
        now_theme_key = theme_dict_swap[now_theme]
        theme_dropdown_list = []
        for key in theme_dict.keys():
            theme_dropdown_list.append(ft.dropdown.Option(key))
        dr_theme = ft.Dropdown(
            label="テーマ",
            hint_text="ライト",
            tooltip="テーマを選択します。保存ボタンを押すと適用されます\n※現在調整中です",
            options=theme_dropdown_list,
            value=now_theme_key,
            disabled=True,
        )

        # 現在の都道府県設定を読み込む
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="utf-8")
        now_prefecture = config["USER"]["location"]
        # 都道府県辞書から設定を読む
        prefecture_dict = prefecture.get_prefecture_dict()
        prefecture_dropdown_list = []
        for key in prefecture_dict.keys():
            prefecture_dropdown_list.append(ft.dropdown.Option(key))
        dr_prefecture = ft.Dropdown(
            label="都道府県",
            hint_text="東京都",
            options=prefecture_dropdown_list,
            # autofocus=True,
            on_change=prefecture_change,
            tooltip="都道府県を選択してください。",
        )
        dr_prefecture_detail = ft.Dropdown(
            label="地名",
            hint_text="新宿",
            options=[ft.dropdown.Option(now_prefecture)],
            value=now_prefecture,
            # on_change=prefecture_detail_change,
            tooltip="上で都道府県を選ぶと選択できます。",
        )
        # ファイルパス設定
        configc = ConfigController()
        # ファイルパス用関数
        def aivoice_pick_directory_result(e: ft.FilePickerResultEvent):
            txf_aivoice.value = e.path + "\\" if e.path else txf_aivoice.value
            txf_aivoice.update()
        pick_directory_dialog = ft.FilePicker(on_result=aivoice_pick_directory_result)
        self.page.overlay.append(pick_directory_dialog)
        txf_aivoice = ft.TextField(tooltip="A.I.VOICE Editorのフォルダを指定してください", label="A.I.VOICE Editorのフォルダパス", col=10, value=configc.read("aivoiceEditorPath"), dense=True)
        row_aivoice = ft.ResponsiveRow(
            controls=[
                txf_aivoice,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_directory_dialog.get_directory_path(
                        dialog_title="A.I.VOICE Editorのフォルダを選択",
                        initial_directory=os.path.dirname(configc.read("aivoiceEditorPath")),
                        ),
                    col=2,
                ),
            ]
        )
        def voicevox_pick_files_result(e : ft.FilePickerResultEvent):
            txf_voicevox.value = e.files[0].path if e.files else txf_voicevox.value
            txf_voicevox.update()
        voicevox_pick_files_dialog = ft.FilePicker(on_result=voicevox_pick_files_result)
        self.page.overlay.append(voicevox_pick_files_dialog)
        txf_voicevox = ft.TextField(tooltip="VOICEVOXのexeファイルを指定してください", label="VOICEVOX.exeのファイルパス", col=10, value=configc.read("voicevoxPath", section="VOICEVOX"), dense=True)
        row_voicevox = ft.ResponsiveRow(
            controls=[
                txf_voicevox,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: voicevox_pick_files_dialog.pick_files(
                        dialog_title="VOICEVOXの実行ファイルを選択",
                        allow_multiple=False,
                        allowed_extensions=["exe"],
                        initial_directory=os.path.dirname(configc.read("voicevoxPath", section="VOICEVOX")),
                    ),
                    col=2,
                ),
            ]
        )
        def coeiroink_pick_files_result(e : ft.FilePickerResultEvent):
            txf_coeiroink.value = e.files[0].path if e.files else txf_coeiroink.value
            txf_coeiroink.update()
        coeiroink_pick_files_dialog = ft.FilePicker(on_result=coeiroink_pick_files_result)
        self.page.overlay.append(coeiroink_pick_files_dialog)
        txf_coeiroink = ft.TextField(tooltip="COEIROINK v2のexeファイルを指定してください", label="COEIROINKv2.exeのファイルパス", col=10, value=configc.read("coeiroinkPath"), dense=True)
        row_coeiroink = ft.ResponsiveRow(
            controls=[
                txf_coeiroink,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: coeiroink_pick_files_dialog.pick_files(
                        dialog_title="COEIROINKの実行ファイルを選択",
                        allow_multiple=False,
                        allowed_extensions=["exe"],
                        initial_directory=os.path.dirname(configc.read("coeiroinkPath")),
                    ),
                    col=2,
                ),
            ]
        )
        def aquestalk_pick_files_result(e : ft.FilePickerResultEvent):
            txf_aquestalk.value = e.files[0].path if e.files else txf_aquestalk.value
            txf_aquestalk.update()
        aquestalk_pick_files_dialog = ft.FilePicker(on_result=aquestalk_pick_files_result)
        self.page.overlay.append(aquestalk_pick_files_dialog)
        txf_aquestalk = ft.TextField(tooltip="AquesTalkPlayerのexeファイルを指定してください", label="AquesTalkPlayer.exeのファイルパス", col=10, value=configc.read("aquestalkPath"), dense=True)
        row_aquestalk = ft.ResponsiveRow(
            controls=[
                txf_aquestalk,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: aquestalk_pick_files_dialog.pick_files(
                        dialog_title="AquesTalkの実行ファイルを選択",
                        allow_multiple=False,
                        allowed_extensions=["exe"],
                        initial_directory=os.path.dirname(configc.read("aquestalkPath")),
                    ),
                    col=2,
                ),
            ]
        )
        # 音声保存
        def voice_pick_directory_result(e: ft.FilePickerResultEvent):
            txf_voice.value = e.path + "\\" if e.path else txf_voice.value
            txf_voice.update()
        pick_directory_dialog = ft.FilePicker(on_result=voice_pick_directory_result)
        self.page.overlay.append(pick_directory_dialog)
        txf_voice = ft.TextField(tooltip="音声を自動保存するフォルダを選んでください", label="合成音声を保存するフォルダパス", col=10, value=configc.read("voiceOutputDirectory"), dense=True)
        row_voice = ft.ResponsiveRow(
            controls=[
                txf_voice,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: pick_directory_dialog.get_directory_path(
                        dialog_title="合成音声を保存するフォルダを選択",
                        initial_directory=os.path.dirname(configc.read("voiceOutputDirectory")),
                        ),
                    col=2,
                ),
            ]
        )
        write_voice_value = None
        try:
            tmp = configc.read("writeVoice").lower()
            if tmp == "true" or tmp == "yes" or tmp == "on":
                write_voice_value = True
            else:
                write_voice_value = False
        except Exception as e:
            print(e)
            write_voice_value = False

        sw_voice_save = ft.Switch(label="合成した音声を指定フォルダに書き出す", value=write_voice_value, adaptive=True)
        def user_avatar_pick_files_result(e : ft.FilePickerResultEvent):
            txf_user_avatar.value = e.files[0].path if e.files else txf_user_avatar.value
            txf_user_avatar.update()
        user_avatar_pick_files_dialog = ft.FilePicker(on_result=user_avatar_pick_files_result)
        self.page.overlay.append(user_avatar_pick_files_dialog)
        txf_user_avatar = ft.TextField(tooltip="ユーザアバターとして使用するアバターファイルを指定してください", label="ユーザアバターのファイル", col=10, value=configc.read("userAvatarPath"), dense=True)
        row_user_avatar = ft.ResponsiveRow(
            controls=[
                txf_user_avatar,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: user_avatar_pick_files_dialog.pick_files(
                        dialog_title="ユーザアバターのファイルを選択",
                        allow_multiple=False,
                        allowed_extensions=["chr"],
                        initial_directory=f".{os.sep}avatar",
                    ),
                    col=2,
                ),
            ]
        )
        sw_user_voice_play = ft.Switch(label="ユーザに設定したボイスを再生する", value=configc.read("userVoicePlay").lower() == "true", adaptive=True)
        sw_user_voice_save = ft.Switch(label="ユーザに設定したボイスを保存する", value=configc.read("userVoiceSave").lower() == "true", adaptive=True)
        # 保存ボタン
        btn_save = ft.FilledButton("設定を保存", icon=ft.icons.SAVE_OUTLINED, tooltip="現在の設定を保存します。一部設定を即座に適用します。", on_click=save_setting)
        self.list_view_setting = ft.ListView(
            controls=[
                ft.Text("保存ボタンを押すまで設定は保存されません。表示内容は開き直すと再読み込みされます。", size=font_template["body"]),
                # テーマ
                ft.Text("テーマ", weight=ft.FontWeight.W_500, size=font_template["headline"]),
                ft.Text(f"現在の設定: {now_theme_key}", size=font_template["body"]),
                dr_theme,
                # 天気
                ft.Text("天気予報", weight=ft.FontWeight.W_500, size=font_template["headline"]),
                ft.Text("現在の設定: " + now_prefecture, size=font_template["body"]),
                dr_prefecture,
                dr_prefecture_detail,
                ft.Text("ここにない地名を選びたい場合、直接setting.iniを編集してください。"),
                # ファイルパス指定
                ft.Text("各ソフトのパス指定", weight=ft.FontWeight.W_500, size=font_template["headline"]),
                row_aivoice,
                row_voicevox,
                row_coeiroink,
                row_aquestalk,
                ft.Text("音声の書き出し", weight=ft.FontWeight.W_500, size=font_template["headline"]),
                row_voice,
                sw_voice_save,
                ft.Text("ユーザアバターの設定", weight=ft.FontWeight.W_500, size=font_template["headline"]),
                row_user_avatar,
                sw_user_voice_play,
                sw_user_voice_save,
            ],
            spacing=10,
            height=self.page.window_height - 200,
            # expand=True,
        )
        # ページ内容
        self.ct_setting_listview = ft.Container(
            content=ft.Column(
                controls=[
                    self.list_view_setting,
                    ft.Row(controls=[btn_save], alignment=ft.MainAxisAlignment.END, height=50),
                ],
                # width=500,
                expand=True,
            ),
            alignment=ft.alignment.top_right,
            # height=self.page.window_height,
        )
        self.ct_setting = ft.Container(
            content=ft.Row(
                controls=[
                    MenuNavi(self.page, index=3),
                    self.ct_setting_listview,
                ]
            ),
        )
        self.appbar = ft.AppBar(
            title=ft.Text("基本設定"), 
            bgcolor=ft.colors.SURFACE_VARIANT,
            toolbar_height=50,
        )
        self.route = "/setting"
        self.controls = [
            self.ct_setting,
        ]
        self.spacing = 0

    def resize(self, window_width, window_height):
        correct_width = window_width - 130
        correct_height = window_height - (self.appbar.toolbar_height + 12)
        self.list_view_setting.height = correct_height - 120
        self.ct_setting_listview.width = correct_width
        self.ct_setting.height = correct_height

    def reload(self):
        pass

class WeatherView(ft.View):
    def __init__(self, page):
        super().__init__()
        self.page = page

        try:
            weather_dict = weather.weather_call_google()
            icon_path = weather.weather_to_icon(weather_dict["weather"])
        except requests.exceptions.ConnectionError as e:
            print(e.args, file=sys.stderr)
            weather_dict = {
                "location": "取得不能",
                "temp" : "不明",
                "time" : "不明",
                "weather" : "失敗"
            }
            icon_path = None
            alert = ft.AlertDialog(title="天気情報の取得に失敗しました", content=ft.Text("デバイスがオフラインであるか、取得元の仕様変更により取得不能になった可能性があります。"))
            self.page.dialog = alert
            alert.open = True
        
        if icon_path is None:
            image = ft.Text("failed")
        else :
            image = ft.Image(src=icon_path)

        row_weather = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(weather_dict["time"] + "時点では"),
                        ft.Row(
                            [
                                ft.Text(weather_dict["location"]),
                                ft.Text(weather_dict["temp"], size=20, weight=ft.FontWeight.W_400),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text(weather_dict["weather"], size=24),
                                image,
                            ]
                        ),
                    ],
                ),
            ],
            width=300,
        )

        self.ct_weather_main = ft.Container(
            content=row_weather,
            height=500,
        )

        self.ct_weather = ft.Container(
            content=ft.Row(
                controls=[
                    MenuNavi(self.page, index=1),
                    self.ct_weather_main,
                ]
            ),
        )

        self.appbar = ft.AppBar(
            title=ft.Text("いまの天気は"),
            bgcolor=ft.colors.SURFACE_VARIANT,
            toolbar_height=50,
        )

        # ページ内容
        self.route = "/weather"
        self.controls = [
            self.ct_weather,
        ]
    def resize(self, window_width, window_height):
        correct_width = window_width - 130
        correct_height = window_height - (self.appbar.toolbar_height + 12)
        self.ct_weather_main.width = correct_width
        self.ct_weather.height = correct_height

    def reload(self):
        pass

class AvatarView(ft.View):
    def __init__(self, page):
        super().__init__()
        self.page : ft.Page = page
        self.now_avatar_file = ""
        self.load_avatar_files()

        configc = ConfigController()
        font_size = int(configc.read("fontSize"))
        font_template = {
            "headline": font_size * 1.5,
            "body": font_size,
        }

        # アバターをすべて読み込みリストに保持
        # avatars = configparser.ConfigParser()
        # avatars.read(Confignames.AVATARS, "UTF-8")
        # items = avatars.items("AVATAR")
        # print(items)

        # イベント
        # ボイスタイプ変更時の処理
        def change_dr_talk(e):
            talk_type = dr_talk.value
            # ドロップダウンメニューの入れ替え
            if talk_type is not None:
                dr_talk_speaker.options = speakers_options[talk_type]
            # UUIDの入力可否
            if talk_type == TalkType.COEIROINK:
                tf_talk_speaker_uuid.disabled = False
            else:
                tf_talk_speaker_uuid.disabled = True
            # パラメータ編集の非表示
            if talk_type == TalkType.AIVOICE or talk_type == TalkType.VOICEVOX or talk_type == TalkType.COEIROINK:
                ct_edit_param.disabled = False
                ct_edit_param_only_aivoice.disabled = True
                if talk_type == TalkType.AIVOICE:
                    ct_edit_param_only_aivoice.disabled = False
            else:
                ct_edit_param.disabled = True
                ct_edit_param_only_aivoice.disabled = True
            # ピッチ項目の入れ替え
            if talk_type == TalkType.AIVOICE:
                sl_voicevox_pitch.visible = False
                tx_voicevox_pitch.visible = False
                sl_aivoice_pitch.visible = True
                tx_aivoice_pitch.visible = True
            elif talk_type == TalkType.VOICEVOX or talk_type == TalkType.COEIROINK:
                sl_voicevox_pitch.visible = True
                tx_voicevox_pitch.visible = True
                sl_aivoice_pitch.visible = False
                tx_aivoice_pitch.visible = False
            tf_talk_speaker_uuid.update()
            sl_voicevox_pitch.update()
            sl_aivoice_pitch.update()
            dr_talk_speaker.update()
            ct_edit_param.update()
            ct_edit_param_only_aivoice.update()

        def change_dr_talk_speaker(e):
            tf_talk_speaker.value = dr_talk_speaker.value
            tf_talk_speaker.update()

        def change_tf_talk_speaker(e):
            dr_talk_speaker.value = tf_talk_speaker.value
            dr_talk_speaker.update()

        def change_slider(value, text_control):
            if type(value) == float:
                text_control.value = '{:.2f}'.format(value)
            else:
                text_control.value = value
            text_control.update()

        # アバターファイル変更時
        def change_current_avatar_file(e):
            avatar_name = e.control.value
            print(f"Edit avatar changed to {avatar_name}")
            selected : Slot = None
            self.now_avatar_file = ""
            for a in self.avatars:
                if a.avatar_name == avatar_name:
                    selected = a
                    self.now_avatar_file = self.avatar_files[a]
                    break
            if selected == None:
                print("存在しないアバターを編集しようとしました", file=sys.stderr)
            tf_name.value = selected.avatar_name
            tf_persona.value = selected.system_prompt
            tf_picture.value = selected.picture_path
            tf_picture_circle.value = selected.picture_circle_path
            cb_talk.value = selected.talk_flag
            dr_talk.value = selected.talk_type
            change_dr_talk(0)
            dr_talk_speaker.value = selected.talk_speaker
            tf_talk_speaker.value = selected.talk_speaker
            tf_talk_speaker_uuid.value = selected.talk_speaker_uuid
            if selected.talk_param is not None:
                sl_speed.value = float(selected.talk_param["speed"])
                tx_speed.value = '{:.2f}'.format(sl_speed.value)
                if selected.talk_type == TalkType.AIVOICE:
                    sl_aivoice_pitch.value = float(selected.talk_param["pitch"])
                    tx_aivoice_pitch.value = '{:.2f}'.format(sl_aivoice_pitch.value)
                elif selected.talk_type == TalkType.VOICEVOX or selected.talk_type == TalkType.COEIROINK:
                    sl_voicevox_pitch.value = float(selected.talk_param["pitch"])
                    tx_voicevox_pitch.value = '{:.2f}'.format(sl_voicevox_pitch.value)
                sl_intonation.value = float(selected.talk_param["intonation"])
                tx_intonation.value = '{:.2f}'.format(sl_intonation.value)
                tx_volume.value = sl_volume.value = float(selected.talk_param["volume"])
                tx_volume.value = '{:.2f}'.format(sl_volume.value)
                sl_pre_phoneme.value = float(selected.talk_param["prePhoneme"])
                tx_pre_phoneme.value = '{:.2f}'.format(sl_pre_phoneme.value)
                sl_post_phoneme.value = float(selected.talk_param["postPhoneme"])
                tx_post_phoneme.value = '{:.2f}'.format(sl_post_phoneme.value)
                tx_middle_pause.value = sl_middle_pause.value = int(selected.talk_param["middle"])
                tx_long_pause.value = sl_long_pause.value = int(selected.talk_param["long"])
                tx_sentence_pause.value = sl_sentence_pause.value = int(selected.talk_param["sentence"])

            ct_edit_chara.update()
            ct_edit_param.update()
            ct_edit_param_only_aivoice.update()

        # 保存ボタンを押したとき
        def edit_avatar_save(_):
            if self.now_avatar_file == "" or self.now_avatar_file is None:
                return
            print(f"Edit avatar save to {self.now_avatar_file} ... ", end="")

            avatar_file_path = f".{os.sep}avatar{os.sep}{self.now_avatar_file}"
            parser = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
            parser.optionxform = str
            parser.read(avatar_file_path, encoding="UTF-8")
            parser["CHARA"]["name"] = tf_name.value
            parser["CHARA"]["persona"] = tf_persona.value
            parser["IMAGE"]["picture_path"] = tf_picture.value
            parser["IMAGE"]["picture_circle_path"] = tf_picture_circle.value
            parser["VOICE"]["talk_flag"] = str(cb_talk.value)
            talk_type = dr_talk.value
            parser["VOICE"]["talk_type"] = talk_type
            parser["VOICE"]["talk_speaker"] = tf_talk_speaker.value
            parser["VOICE"]["talk_speaker_uuid"] = tf_talk_speaker_uuid.value
            parser["PARAM"]["speedScale"] = '{:.2f}'.format(sl_speed.value)
            parser["PARAM"]["pitchScale"] = '{:.2f}'.format(sl_aivoice_pitch.value)
            if talk_type == TalkType.VOICEVOX or talk_type == TalkType.COEIROINK:
                parser["PARAM"]["pitchScale"] = '{:.2f}'.format(sl_voicevox_pitch.value)
            parser["PARAM"]["intonationScale"] = '{:.2f}'.format(sl_intonation.value)
            parser["PARAM"]["prePhonemeLength"] = '{:.2f}'.format(sl_pre_phoneme.value)
            parser["PARAM"]["postPhonemeLength"] = '{:.2f}'.format(sl_post_phoneme.value)
            parser["AIVOICEPARAM"]["middlePause"] = f"{sl_middle_pause.value}"
            parser["AIVOICEPARAM"]["longPause"] = f"{sl_long_pause.value}"
            parser["AIVOICEPARAM"]["sentencePause"] = f"{sl_sentence_pause.value}"

            with open(avatar_file_path, encoding="UTF-8", mode="w") as file:
                parser.write(file)

            print("Success")
            # スナックバーの表示
            self.page.snack_bar = ft.SnackBar(ft.Text(f"{self.now_avatar_file}へ保存しました。"))
            self.page.snack_bar.open = True
            self.page.update()

        self.dr_edit_avatars = ft.Dropdown(
            label="アバターファイル名",
            hint_text="Character",
            tooltip="本体フォルダ内のavatarフォルダに置かれている.chrファイル一覧",
            options=[ft.dropdown.Option(avatar.avatar_name) for avatar in self.avatars],
            value="",
            on_change=change_current_avatar_file,
            expand=True,
            dense=True,
            text_size=font_template["body"],
        )
        # キャラ
        tf_name = ft.TextField(
            label="アバター名",
            hint_text="ずんだもん",
            tooltip="チャット画面で表示される名称",
            dense=True,
        )
        tf_persona = ft.TextField(
            label="性格",
            hint_text="性格を入力",
            tooltip="GPTに伝えるシステムプロンプト。記述次第で応対が変わります",
            dense=True,
            multiline=True,
            min_lines=3,
            max_lines=10,
        )
        # 画像
        tf_picture = ft.TextField(
            label="立ち絵(png, jpg)",
            hint_text=".\\image\\image.png",
            tooltip="チャットで表示される画像を選択",
            dense=True,
            col=10,
        )
        def picture_pick_file_result(e: ft.FilePickerResultEvent):
            tf_picture.value = e.path + os.sep if e.path else tf_picture.value
            tf_picture.update()
        pick_picture_dialog = ft.FilePicker(on_result=picture_pick_file_result)
        self.page.overlay.append(pick_picture_dialog)
        row_picture = ft.ResponsiveRow(
            controls=[
                tf_picture,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.FILE_OPEN,
                    on_click=lambda _: pick_picture_dialog.pick_files(
                        dialog_title="立ち絵画像を選択",
                        allow_multiple=False,
                        allowed_extensions=["png", "jpg", "jpeg"],
                        initial_directory=f".{os.sep}"
                    ),
                    col=2,
                )
            ]
        )
        tf_picture_circle = ft.TextField(
            label="アバターアイコン(png, jpg)",
            hint_text=".\\image\\image.png",
            tooltip="チャットで表示されるアイコン用画像を選択",
            dense=True,
            col=10,
        )
        def picture_circle_pick_file_result(e: ft.FilePickerResultEvent):
            tf_picture_circle.value = e.path + os.sep if e.path else tf_picture_circle.value
            tf_picture_circle.update()
        pick_picture_circle_dialog = ft.FilePicker(on_result=picture_circle_pick_file_result)
        self.page.overlay.append(pick_picture_circle_dialog)
        row_picture_circle = ft.ResponsiveRow(
            controls=[
                tf_picture_circle,
                ft.ElevatedButton(
                    "選択",
                    icon=ft.icons.FILE_OPEN,
                    on_click=lambda _: pick_picture_circle_dialog.pick_files(
                        dialog_title="立ち絵画像を選択",
                        allow_multiple=False,
                        allowed_extensions=["png", "jpg", "jpeg"],
                        initial_directory=f".{os.sep}"
                    ),
                    col=2,
                )
            ]
        )
        # ボイス
        talk_types = [
            ft.dropdown.Option(key=TalkType.AIVOICE, text="A.I.VOICE"),
            ft.dropdown.Option(key=TalkType.VOICEVOX, text="VOICEVOX"),
            ft.dropdown.Option(key=TalkType.COEIROINK, text="COEIROINK"),
            ft.dropdown.Option(key=TalkType.AQUESTALK, text="AquesTalk"),
        ]
        cb_talk = ft.Checkbox(label="合成音声を行う")
        
        dr_talk = ft.Dropdown(
            label="ボイスタイプ",
            hint_text="VOICEVOX",
            tooltip="どのエディタを使うのか選択",
            options=talk_types,
            dense=True,
            on_change=change_dr_talk,
        )
        
        tf_talk_speaker = ft.TextField(
            label="speaker_id・プリセット名",
            hint_text="VOICEVOX・COEIROINK: 0 A.I.VOICE: 結月ゆかり",
            tooltip="VOICEVOXとCOEIROINKでは整数でIDを指定します。\nA.I.VOICEやAquesTalkではボイスプリセット名を指定します。",
            dense=True,
            on_change=change_tf_talk_speaker,
        )
        voicevox_speakers = [
            ft.dropdown.Option(key="3", text="3: ずんだもん ノーマル"),
            ft.dropdown.Option(key="1", text="1: ずんだもん あまあま"),
            ft.dropdown.Option(key="7", text="7: ずんだもん ツンツン"),
            ft.dropdown.Option(key="5", text="5: ずんだもん セクシー"),
            ft.dropdown.Option(key="22", text="22: ずんだもん ささやき"),
            ft.dropdown.Option(key="38", text="38: ずんだもん ひそひそ"),
            ft.dropdown.Option(key="2", text="2: 四国めたん ノーマル"),
            ft.dropdown.Option(key="0", text="0: 四国めたん あまあま"),
            ft.dropdown.Option(key="6", text="6: 四国めたん ツンツン"),
            ft.dropdown.Option(key="4", text="4: 四国めたん セクシー"),
            ft.dropdown.Option(key="36", text="36: 四国めたん ささやき"),
            ft.dropdown.Option(key="37", text="37: 四国めたん ひそひそ"),
            ft.dropdown.Option(key="8", text="8: 春日部つむぎ ノーマル"),
            ft.dropdown.Option(key="14", text="14: 冥鳴ひまり ノーマル"),
            ft.dropdown.Option(key="10", text="10: 雨晴はう ノーマル"),
            ft.dropdown.Option(key="9", text="9: 波音リツ ノーマル"),
            ft.dropdown.Option(key="20", text="20: もち子さん ノーマル"),
            ft.dropdown.Option(key="29", text="29: No.7 ノーマル"),
            ft.dropdown.Option(key="30", text="30: No.7 アナウンス"),
            ft.dropdown.Option(key="31", text="31: No.7 読み聞かせ"),
            ft.dropdown.Option(key="23", text="23: WhiteCUL ノーマル"),
            ft.dropdown.Option(key="26", text="26: WhiteCUL びえーん"),
        ]
        coeiroink_speakers = [
            ft.dropdown.Option(key="0", text="0: つくよみちゃん"),
            ft.dropdown.Option(key="", text=""),
        ]
        aivoice_speakers = [
            ft.dropdown.Option("結月ゆかり"),
            ft.dropdown.Option("紲星あかり"),
            ft.dropdown.Option("琴葉茜"),
            ft.dropdown.Option("琴葉葵"),
            ft.dropdown.Option("栗田まろん"),
        ]
        aquestalk_speakers = [
            ft.dropdown.Option("れいむ"),
            ft.dropdown.Option("まりさ"),
            ft.dropdown.Option("こいし"),
            ft.dropdown.Option("さとり"),
            ft.dropdown.Option("女性１"),
            ft.dropdown.Option("女性２"),
            ft.dropdown.Option("男声１"),
            ft.dropdown.Option("男声２"),
            ft.dropdown.Option("ロボット"),
        ]
        speakers_options = {
            TalkType.VOICEVOX: voicevox_speakers,
            TalkType.COEIROINK: coeiroink_speakers,
            TalkType.AIVOICE: aivoice_speakers,
            TalkType.AQUESTALK: aquestalk_speakers,
        }
        dr_talk_speaker = ft.Dropdown(
            label="speaker_id・プリセット名の候補",
            hint_text="0: ずんだもん",
            tooltip="事前定義済みspeaker_id・プリセット名から候補を探します",
            options=[],
            dense=True,
            on_change=change_dr_talk_speaker,
        )
        tf_talk_speaker_uuid = ft.TextField(
            label="speaker_uuid",
            hint_text="3c37646f-3881-5374-2a83-149267990abc",
            tooltip="COEIROINKでのみ用いられるキャラごとのユニークなIDです。COEIROINK本体フォルダのspeaker_infoを適宜参照してください。MYCOEでは通常speaker_info内のフォルダ名とUUIDは同一です。",
            dense=True,
        )

        # ボイスパラメータのスライダーとラベル
        slider_width = 400
        sl_speed = ft.Slider(min=0.50, max=2.00, value=1.00, divisions=150, label="x{value}", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_speed))
        tx_speed = ft.Text("1.00")
        sl_aivoice_pitch = ft.Slider(min=0.50, max=2.00, value=1.00, divisions=150, label="x{value}", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_aivoice_pitch))
        tx_aivoice_pitch = ft.Text("1.00")
        sl_voicevox_pitch = ft.Slider(min=-0.15, max=0.15, value=0.00,divisions=30, label="{value}", round=2, width=slider_width, visible=False, on_change=lambda e: change_slider(e.control.value, tx_voicevox_pitch))
        tx_voicevox_pitch = ft.Text("0.00", visible=False)
        sl_volume = ft.Slider(min=0.00, max=2.00, value=1.00, divisions=200, label="x{value}", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_volume))
        tx_volume = ft.Text("1.00")
        sl_intonation = ft.Slider(min=0.00, max=2.00, value=1.00, divisions=200, label="x{value}", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_intonation))
        tx_intonation = ft.Text("1.00")
        sl_pre_phoneme = ft.Slider(min=0.00, max=1.50, value=0.10, divisions=150, label="{value}s", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_pre_phoneme))
        tx_pre_phoneme = ft.Text("0.10")
        sl_post_phoneme = ft.Slider(min=0.00, max=1.50, value=0.10, divisions=150, label="{value}s", round=2, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_post_phoneme))
        tx_post_phoneme = ft.Text("0.10")
        sl_middle_pause = ft.Slider(min=80, max=500, value=160, divisions=420, label="{value}ms", round=0, width=slider_width, tooltip="最小値80ms、最大値500ms、デフォルト150ms", on_change=lambda e: change_slider(e.control.value, tx_middle_pause))
        tx_middle_pause = ft.Text("80")
        sl_long_pause = ft.Slider(min=80, max=2000, value=370, divisions=1920, label="{value}ms", round=0, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_long_pause))
        tx_long_pause = ft.Text("370")
        sl_sentence_pause = ft.Slider(min=0, max=10000, value=800, divisions=10000, label="{value}ms", round=0, width=slider_width, on_change=lambda e: change_slider(e.control.value, tx_sentence_pause))
        tx_sentence_pause = ft.Text("800")

        ct_edit_chara = ft.Container(
            ft.Column(
                [
                    ft.Row(controls=[self.dr_edit_avatars,]),
                    ft.Divider(),
                    ft.Text("キャラ設定", size=font_template["headline"], weight=ft.FontWeight.W_500),
                    tf_name,
                    tf_persona,
                    ft.Text("画像設定", size=font_template["headline"], weight=ft.FontWeight.W_500),
                    row_picture,
                    row_picture_circle,
                    ft.Text("ボイス設定", size=font_template["headline"], weight=ft.FontWeight.W_500),
                    cb_talk,
                    ft.Text("チェックを外すと音声合成も出力もされません。"),
                    dr_talk,
                    dr_talk_speaker,
                    ft.Text("このリストから選ぶと下2つの項目が自動入力されます。エディタ側の仕様変更やボイスプリセット名変更により自動入力は間違ったものになる可能性があります。COEIROINKのみspeaker_uuidが必要です。", size=font_template["body"]),
                    tf_talk_speaker,
                    tf_talk_speaker_uuid,
                ]
            )
        )

        ct_edit_param = ft.Container(
            ft.Column(
                [
                    ft.Text("ボイスパラメータ", size=font_template["headline"], weight=ft.FontWeight.W_500),
                    ft.Row([ft.Text("話速　　　"), tx_speed, sl_speed]),
                    ft.Row([ft.Text("音高　　　"), tx_aivoice_pitch, tx_voicevox_pitch, sl_aivoice_pitch, sl_voicevox_pitch]),
                    ft.Row([ft.Text("音量　　　"), tx_volume, sl_volume]),
                    ft.Row([ft.Text("抑揚　　　"), tx_intonation, sl_intonation]),
                    ft.Row([ft.Text("開始時無音"), tx_pre_phoneme, sl_pre_phoneme]),
                    ft.Row([ft.Text("終了時無音"), tx_post_phoneme, sl_post_phoneme]),
                ]
            )
        )
        ct_edit_param_only_aivoice = ft.Container(
            ft.Column(
                [
                    ft.Text("ボイスパラメータ(A.I.VOICEのみ)", size=font_template["headline"], weight=ft.FontWeight.W_500),
                    ft.Text("これらのパラメータはA.I.VOICEにのみ適用されます。", size=font_template["body"]),
                    ft.Row([ft.Text("短ポーズ　"), tx_middle_pause, sl_middle_pause]),
                    ft.Row([ft.Text("長ポーズ　"), tx_long_pause, sl_long_pause]),
                    ft.Row([ft.Text("文末ポーズ"), tx_sentence_pause, sl_sentence_pause]),
                ]
            )
        )
        # アバター編集表示のメイン
        lv_edit_avatar = ft.ListView(
            controls=[
                ft.Divider(opacity=0, thickness=1),
                ct_edit_chara,
                ct_edit_param,
                ct_edit_param_only_aivoice,
            ],
            spacing=10,
            expand=True,
        )

        bt_edit_save = ft.FilledButton(
            "保存",
            tooltip="現在の内容で保存します。適用するにはソフトの再起動が必要です。",
            icon=ft.icons.SAVE_OUTLINED,
            on_click=edit_avatar_save,
        )
        cl_edit_avatar = ft.Column(
            controls=[
                lv_edit_avatar,
                ft.Row(
                    controls=[bt_edit_save],
                    height=50,
                    alignment=ft.MainAxisAlignment.END,
                ),
            ]
        )

        def add_avatar_file(e):
            file_name = f"{tx_avatar_file_name.value}.chr"
            print(file_name)
            file_path = f".{os.sep}avatar{os.sep}{file_name}"
            try:
                if os.path.isfile(file_path):
                    alert = ft.AlertDialog(title=ft.Text(f"{file_path}はすでにあります"), content=ft.Text("ファイル名を変更するか、削除してしてください。ファイルの作成は失敗しました。"))
                    self.page.dialog = alert
                    alert.open = True
                    self.page.update()
                    raise FileExistsError(f"{file_path} is already exsists")
            except FileExistsError as e:
                print(e.args, file=sys.stderr)
                return
            try:
                with open(file_path, "w", encoding="UTF-8") as f:
                    parser = configparser.ConfigParser()
                    parser.read(file_path, encoding="UTF-8")
                    parser.optionxform = str
                    # parser.add_section("DEFAULT")
                    parser.add_section("CHARA")
                    parser.add_section("IMAGE")
                    parser.add_section("VOICE")
                    parser.add_section("PARAM")
                    parser.add_section("AIVOICEPARAM")
                    DEFAULT = "DEFAULT"
                    CHARA = "CHARA"
                    IMAGE = "IMAGE"
                    VOICE = "VOICE"
                    PARAM = "PARAM"
                    AIVOICEPARAM = "AIVOICEPARAM"
                    parser[DEFAULT]["blank"] = ""
                    
                    parser[CHARA]["name"] = "new avatar"
                    parser[CHARA]["persona"] = "性格なし"
                    parser[IMAGE]["picture_path"] = ""
                    parser[IMAGE]["picture_circle_path"] = ""
                    parser[VOICE]["talk_flag"] = "True"
                    parser[VOICE]["talk_type"] = TalkType.VOICEVOX
                    parser[VOICE]["talk_speaker"] = "0"
                    parser[VOICE]["talk_speaker_uuid"] = ""
                    parser[PARAM]["speedScale"] = "1.00"
                    parser[PARAM]["pitchScale"] = "0.00"
                    parser[PARAM]["intonationScale"] = "1.00"
                    parser[PARAM]["volumeScale"] = "1.00"
                    parser[PARAM]["prePhonemeLength"] = "0.10"
                    parser[PARAM]["postPhonemeLength"] = "0.10"
                    parser[AIVOICEPARAM]["middlePause"] = "150"
                    parser[AIVOICEPARAM]["longPause"] = "370"
                    parser[AIVOICEPARAM]["sentencePause"] = "800"
                    parser[AIVOICEPARAM]["presetFlag"] = "True"
                    parser[AIVOICEPARAM]["presetVolume"] = "1.00"
                    parser[AIVOICEPARAM]["presetSpeed"] = "1.00"
                    parser[AIVOICEPARAM]["presetPitch"] = "1.00"
                    parser[AIVOICEPARAM]["presetPitchRange"] = "2.00"
                    parser[AIVOICEPARAM]["presetMiddlePause"] = "150"
                    parser[AIVOICEPARAM]["presetLongPause"] = "400"
                    parser.write(f)
                print(f"Add avatar file {file_path}")
                # スナックバーの表示
                self.page.snack_bar = ft.SnackBar(ft.Text(f"{file_path}を新規作成しました。"))
                self.page.snack_bar.open = True
                self.reload()
                self.page.update()
            except OSError as e:
                print(e.args, file=sys.stderr)
        
        def delete_avatar_file(e):
            avatar_name = self.dr_delete_avatar.value
            selected : Slot = None
            selected_avatar_file_name = ""
            for a in self.avatars:
                if a.avatar_name == avatar_name:
                    selected = a
                    selected_avatar_file_name = self.avatar_files[a]
                    break
            if selected == None:
                print("存在しないアバターを削除しようとしました")
            avatar_file_path = f".{os.sep}avatar{os.sep}{selected_avatar_file_name}"

            def click_dialog(flag):
                alert.open = False
                self.page.update()
                if flag:
                    # 削除実行
                    print(f"Delete avatar {selected_avatar_file_name}")
                    os.remove(f".{os.sep}avatar{os.sep}{selected_avatar_file_name}")
                    self.reload()
                    self.page.update()

            ok = ft.TextButton("OK", on_click=lambda _: click_dialog(True))
            ng = ft.TextButton("やっぱやめる", on_click=lambda _: click_dialog(False))
            alert = ft.AlertDialog(
                title=ft.Text("本当に削除してもいいですか？"), 
                content=ft.Text(f"{selected_avatar_file_name}を削除します。"),
                actions=[ok, ng],
            )
            self.page.dialog = alert
            alert.open = True
            self.page.update()

        tx_avatar_file_name = ft.TextField(
            label="アバターファイル名", 
            hint_text="character", 
            suffix_text=".chr", 
            expand=True,
            dense=True,
        )

        bt_avatar_add = ft.ElevatedButton("追加", icon=ft.icons.ADD, on_click=add_avatar_file)

        self.dr_delete_avatar = ft.Dropdown(
            label="アバターファイル名",
            hint_text="Character",
            tooltip="本体フォルダ内のavatarフォルダに置かれている.chrファイル一覧",
            options=[ft.dropdown.Option(avatar.avatar_name) for avatar in self.avatars],
            value="",
            # on_change=,
            expand=True,
            dense=True,
            text_size=font_template["body"],
        )

        bt_delete_avatar = ft.ElevatedButton("削除", icon=ft.icons.DELETE, on_click=delete_avatar_file)

        cl_add_avatar = ft.Column(
            controls=[
                ft.Divider(opacity=0, thickness=1),
                ft.Text("アバターファイルの追加", size=font_template["headline"]),
                ft.Divider(),
                ft.Row([tx_avatar_file_name, bt_avatar_add]),
                ft.Text("アバターファイル名を決めてください。このファイル名は既存のファイルと被らなければどんな名前でも関係ありませんが、後から変更することは難しいです。", size=font_template["body"]),
                ft.Text("アバターファイルの削除", size=font_template["headline"]),
                ft.Divider(),
                ft.Row(
                    [
                        self.dr_delete_avatar,
                        bt_delete_avatar,
                    ]
                ),
            ],
        )

        # 有効化済みアバターをすべて読み込みリストに保持
        avatar_parser = configparser.ConfigParser()
        avatar_parser.read(Confignames.AVATARS, "UTF-8")
        # avatar_parser_items = avatar_parser.items("AVATAR")
        launch_id = int(avatar_parser["OTHER"]["launch_id"])

        def save_activate_avatar():
            avatar_parser = configparser.ConfigParser()
            avatar_parser.read(Confignames.AVATARS, "UTF-8")
            launch_id = int(tf_launch_id.value) if int(tf_launch_id.value) >= 0 else 0
            avatar_parser["OTHER"]["launch_id"] = str(launch_id)
            avatar_parser.remove_section("AVATAR")
            avatar_parser.add_section("AVATAR")
            count = 0
            for row in self.activate_rows:
                avatar_file_name = row.avatar_file_name
                activate = row.activate
                if activate:
                    avatar_parser["AVATAR"][str(count)] = f"avatar{os.sep}{avatar_file_name}"
                    count += 1
            print("Writting to avatars.ini")
            with open(f"config{os.sep}avatars.ini", "w", encoding="UTF-8") as f:
                avatar_parser.write(f)
            # スナックバーの表示
            self.page.snack_bar = ft.SnackBar(ft.Text(f"有効化設定を保存しました。"))
            self.page.snack_bar.open = True
            self.reload()
            self.page.update()

        tf_launch_id = ft.TextField(
            value=launch_id,
            hint_text="0",
            tooltip="起動時何番目のキャラクターを表示するかを0から指定する。有効化済みアバターのうち上から順番に0,1,2...の順番",
            input_filter=ft.NumbersOnlyInputFilter(),
            dense=True,
        )

        self.cl_activate_avatar = ft.Column()

        lv_activate_avatar = ft.ListView(
            [
                ft.Row(
                    [
                        ft.Text("有効化したいキャラクターを選んで保存"),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("起動時何番目を選択するか"),
                        tf_launch_id,
                    ]
                ),
                self.cl_activate_avatar,  
            ],
            spacing=10,
            expand=True,
        )

        cl_activate_avatar = ft.Column(
            [
                ft.Divider(opacity=0),
                lv_activate_avatar,
                ft.Row(
                    [ft.FilledButton(text="保存", icon=ft.icons.SAVE, on_click=lambda _: save_activate_avatar())],
                    height=50,
                    alignment=ft.MainAxisAlignment.END,
                )
            ],
        )
        self.load_activate_avatar()

        # タブ表示　コンテナを複数並べられる
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    tab_content=ft.Container(ft.Row([ft.Icon(ft.icons.EDIT), ft.Text("編集")]), tooltip="アバターファイルの編集ができます。表示名、性格、画像、ボイスなどの設定ができます。\nチャット画面への表示・非表示は「有効化」セクションで行います。"),
                    content=ft.Container(content=cl_edit_avatar, alignment=ft.alignment.top_right),
                ),
                ft.Tab(
                    tab_content=ft.Container(
                        ft.Row([ft.Icon(ft.icons.ADD), ft.Text("追加・削除")]), 
                        tooltip="アバターファイルの追加・削除を行います。"
                    ),
                    content=ft.Container(content=cl_add_avatar, alignment=ft.alignment.top_right),
                ),
                ft.Tab(
                    tab_content=ft.Container(
                        ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINED), ft.Text("有効化")]), 
                        tooltip="アバターの有効化を行います。デフォルトで表示するアバターの指定もできます。"
                    ),
                    content=ft.Container(content=cl_activate_avatar, alignment=ft.alignment.top_right),
                ),
            ],
            expand=1,
        )

        # もっとも外側のコンテナ
        self.ct_avatar = ft.Container(
            content=ft.Row(
                controls=[
                    MenuNavi(page, index=2),
                    self.tabs,
                ],
                expand=True,
                spacing=10,
            )
        )

        self.route = "/avatar"
        self.appbar = ft.AppBar(
            title=ft.Text("アバターの編集"),
            bgcolor=ft.colors.SURFACE_VARIANT,
            toolbar_height=50
        )
        self.controls = [
            self.ct_avatar
        ]

    def load_avatar_files(self):
        # avatarディレクトリの全.chrファイルを列挙
        s = os.sep
        self.avatar_files = {}
        self.avatars : list[Slot] = []
        for file in os.listdir(f".{s}avatar"):
            base, ext = os.path.splitext(file)
            if ext == ".chr":
                try:
                    slot = Slot(f".{s}avatar{s}{file}")
                    self.avatar_files[slot] = file
                    self.avatars.append(slot)
                except Exception as e:
                    print(e.with_traceback())
                    alert = ft.AlertDialog(title=ft.Text("アバターファイルの読み込みに失敗しました"), content=ft.Text("記述形式が間違っている可能性があります。すべてのパラメータを記述してください"))
                    self.page.dialog = alert
                    alert.open = True

    def load_activate_avatar(self):
        avatar_parser = configparser.ConfigParser()
        avatar_parser.read(Confignames.AVATARS, "UTF-8")
        avatar_parser_items = avatar_parser.items("AVATAR")
        self.activate_rows = []
        for avatar_file_name in self.avatar_files.values():
            is_activated = False
            for activated_avatar_name in avatar_parser_items:
                if avatar_file_name == os.path.basename(activated_avatar_name[1]):
                    is_activated = True
            self.activate_rows.append(ActivateAvatarRow(avatar_file_name, is_activated))
        self.cl_activate_avatar.controls = self.activate_rows

    def resize(self, window_width, window_height):
        correct_width = window_width - 140
        correct_height = window_height - (self.appbar.toolbar_height + 12)
        self.tabs = correct_width
        self.ct_avatar.height = correct_height - 50 # タブメニューの分補正

    def reload(self):
        self.load_avatar_files()
        self.load_activate_avatar()
        self.dr_edit_avatars.options = [ft.dropdown.Option(avatar.avatar_name) for avatar in self.avatars]
        self.dr_delete_avatar.options = [ft.dropdown.Option(avatar.avatar_name) for avatar in self.avatars]