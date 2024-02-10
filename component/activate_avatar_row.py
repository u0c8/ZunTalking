import flet as ft

class ActivateAvatarRow(ft.UserControl):
    def __init__(self, avatar_file_name: str, activate: bool = False):
        super().__init__()
        self.avatar_file_name = avatar_file_name
        self.activate = activate

    def build(self):
        def change_activate_switch(e):
            self.activate = e.control.value

        return ft.Row(
            [
                ft.Switch(value=self.activate, on_change=change_activate_switch),
                ft.Text(self.avatar_file_name),
            ]
        )
    