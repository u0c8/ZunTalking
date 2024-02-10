import flet as ft

# ナビのコンポーネント
class MenuNavi(ft.UserControl):
    def __init__(self, page, index=0):
        super().__init__()
        self.page = page
        self.index = index

    def build(self):
        def change(e):
            selected_index = e.control.selected_index
            # selected_indexによって遷移先ページを変える
            if selected_index == 0:
                # メイン画面
                route = "/"
            elif selected_index == 1:
                route = "/weather"
            elif selected_index == 2:
                route = "/avatar"
            elif selected_index == 3:
                route = "/setting"
            e.control.selected_index = self.index
            e.control.update()
            self.page.go(route)
        # ナビゲーションレイル
        try:
            height = self.page.window_height
        except:
            height = 100
        return ft.Container(
            content=ft.NavigationRail(
                # min_width=100,
                # min_extended_width=200, 
                width=80,
                selected_index=self.index,
                # expand=True,
                destinations=[
                    ft.NavigationRailDestination(
                        icon_content=ft.Icon(name=ft.icons.CHAT_BUBBLE_OUTLINE, tooltip="チャット画面に移動"),
                        selected_icon_content=ft.Icon(name=ft.icons.CHAT_BUBBLE, tooltip="チャット画面"),
                        label="チャット",
                    ),
                    ft.NavigationRailDestination(
                        icon_content=ft.Icon(name=ft.icons.WB_SUNNY_OUTLINED, tooltip="天気予報を調べる"),
                        selected_icon=ft.icons.WB_SUNNY,
                        label="天気",
                    ),
                    ft.NavigationRailDestination(
                        icon_content=ft.Icon(name=ft.icons.PEOPLE_OUTLINED, tooltip="アバターの定義ファイルを変更、追加する"),
                        selected_icon=ft.icons.PEOPLE,
                        label="アバター",
                    ),
                    ft.NavigationRailDestination(
                        icon_content=ft.Icon(name=ft.icons.SETTINGS_OUTLINED, tooltip="設定を簡易的に変更する"),
                        selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                        label="設定",
                    ),
                ],
                on_change=lambda e: change(e),
            ),
            alignment=ft.alignment.top_left,
            # height=height,
        )