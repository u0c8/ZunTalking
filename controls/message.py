import flet as ft
from avatar import Avatar
from configcontrol import ConfigController

# チャットにおけるメッセージのクラス
class Message():
    def __init__(self, sender_avatar : Avatar, sender_name : str, text : str, message_type : str) -> None:
        self.sender_avatar = sender_avatar
        self.sender_name = sender_name
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        # メッセージの位置決定
        align : ft.MainAxisAlignment = None
        if message.message_type == "chat_user":
            align = ft.MainAxisAlignment.END
        elif message.message_type == "chat_gpt":
            align = ft.MainAxisAlignment.START
        # 本文と名前を縦並びにする
        # light_color = ["white70", "black"]
        # dark_color = ["white30", "white70"]
        # maincolor = ""
        # subcolor = ""
        configc = ConfigController()
        self.font_size = int(configc.read("fontSize"))

        self.colum = ft.Column(
            [
                ft.Text(message.sender_avatar.avatar_name, weight="bold", size=int(self.font_size * 0.8)),
                ft.Container(content=ft.Text(
                        message.text, 
                        selectable=True, 
                        expand=True,
                        width=300,  # 本文の幅。固定しないとはみ出る
                        size=self.font_size,
                    ),
                    bgcolor=ft.colors.GREEN_50,
                    padding=10,
                    border_radius=10,
                ),
            ],
            tight=True,
            spacing=5,
            wrap=True,
        )
        # メッセージのRow。行内での位置を変更できる
        self.row = ft.Row(
            controls=[
                self.colum,
            ],
            alignment=align,
        )
        # メッセージの箱。行全体の大きさを指定
        self.container = ft.Container(
            content=self.row,
            width=500,
            # bgcolor=ft.colors.BLUE,
            expand=True,
        )
        circle = ft.CircleAvatar(
            content=ft.Image(src=message.sender_avatar.picture_circle_path),
            color=ft.colors.WHITE,
            # bgcolor=ft.colors.BLACK,
        )
        control_list : list[ft.Control] = None
        if message.message_type == "chat_user":
            control_list = [self.container, circle]
        elif message.message_type == "chat_gpt":
            control_list = [circle, self.container]
        self.controls = control_list

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize()

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]
    
    def set_width(self, width : int) :
        self.width = width
        self.colum.width = width