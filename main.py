from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast

import os
import shutil


class FastAPIProjectGeneratorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_path,
        )
        self.destination_path = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        # Input field for project name
        self.project_name_input = MDTextField(
            hint_text="Enter project name",
            size_hint=(1, None),
            height=50,
        )
        layout.add_widget(self.project_name_input)

        # Button to select destination path
        self.choose_path_button = MDRaisedButton(
            text="Choose Destination Path",
            size_hint=(1, None),
            height=50,
            on_release=self.open_file_manager,
        )
        layout.add_widget(self.choose_path_button)

        # Button to generate the project
        self.generate_button = MDRaisedButton(
            text="Generate Project",
            size_hint=(1, None),
            height=50,
            on_release=self.generate_project,
        )
        layout.add_widget(self.generate_button)

        # Status label
        self.status_label = MDLabel(
            text="",
            size_hint=(1, None),
            height=30,
            theme_text_color="Hint",
        )
        layout.add_widget(self.status_label)

        return layout

    def open_file_manager(self, instance):
        """Open the file manager to select a destination path."""
        self.file_manager.show("/")  # Start browsing from the root directory

    def select_path(self, path):
        """Set the selected path as the destination."""
        self.destination_path = path
        self.status_label.text = f"Destination: {path}"
        toast(f"Path selected: {path}")
        self.exit_file_manager()

    def exit_file_manager(self, *args):
        """Close the file manager."""
        self.file_manager.close()

    def generate_project(self, instance):
        """Generate the FastAPI project."""
        project_name = self.project_name_input.text

        if not project_name:
            self.status_label.text = "[color=ff0000]Project name cannot be empty![/color]"
            toast("Project name is required!")
            return

        if not self.destination_path:
            self.status_label.text = "[color=ff0000]Please select a destination path![/color]"
            toast("Select a destination path first!")
            return

        template_dir = os.path.join(os.path.dirname(__file__), "fastapi_template")
        destination_dir = os.path.join(self.destination_path, project_name)

        try:
            if os.path.exists(destination_dir):
                self.status_label.text = "[color=ff0000]Project already exists![/color]"
                toast("Project already exists!")
                return

            shutil.copytree(template_dir, destination_dir)

            self.status_label.text = f"[color=00ff00]Project '{project_name}' created successfully![/color]"
            toast(f"Project '{project_name}' created!")
        except Exception as e:
            self.status_label.text = f"[color=ff0000]Error: {str(e)}[/color]"
            toast(f"Error: {str(e)}")


if __name__ == "__main__":
    FastAPIProjectGeneratorApp().run()
