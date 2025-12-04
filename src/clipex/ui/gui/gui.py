from kivy.app import App
from kivy.uix.label import Label


class MyApp(App):
    def build(self):
        # The build() method returns the root widget
        return Label(text="Hello, World!", font_size=32)


def main():
    MyApp().run()


if __name__ == "__main__":
    main()
