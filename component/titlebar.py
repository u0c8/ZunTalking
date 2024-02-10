from typing import List, Optional
import flet as ft
from flet_core.control import Control, OptionalNumber
from flet_core.ref import Ref

class WindowTitleBar(ft.UserControl):
    def __init__(self, title, page):
        super().__init__()
        self.page = page
        self.title = title

    def build(self):
        dragarea = ft.WindowDragArea(
            ft.Row(
                [
                    ft.Container(
                        # アプリアイコン
                        ft.Icon(),
                    ),
                    ft.Text(
                        self.title,
                        color=ft.colors.SECONDARY,
                    ),
                ],
            ),
            expand=True,  
        )
        return ft.Container(
            ft.Row(
                [
                    dragarea,
                ]
            ),
            bgcolor=ft.colors.PRIMARY_CONTAINER,
        )
    
class WindowAppBar(ft.AppBar):
    def __init__(self, ref: Ref | None = None, leading: Control | None = None, leading_width: OptionalNumber = None, automatically_imply_leading: bool | None = None, title: Control | None = None, center_title: bool | None = None, toolbar_height: OptionalNumber = None, color: str | None = None, bgcolor: str | None = None, elevation: OptionalNumber = None, actions: List[Control] | None = None):
        super().__init__(ref, leading, leading_width, automatically_imply_leading, title, center_title, toolbar_height, color, bgcolor, elevation, actions)

    def _build(self):
        return ft.WindowDragArea(content=super()._build(), expand=True)