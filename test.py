import webview
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout


class DiagramEditorApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        # Bouton pour ouvrir l'éditeur dans une fenêtre webview
        open_editor_button = Button(text="Open Diagram Editor")
        open_editor_button.bind(on_press=self.open_editor)

        layout.add_widget(open_editor_button)
        return layout

    def open_editor(self, instance):
        # Créer une fenêtre webview avec l'éditeur HTML
        webview.create_window("Diagram Editor", "editor.html")
        webview.start()


if __name__ == "__main__":
    DiagramEditorApp().run()
