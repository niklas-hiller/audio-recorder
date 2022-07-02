from time import sleep
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.image import Image

class MainLayout(FloatLayout):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._recordBtn = Button(
            size_hint = (None, 0.3),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/microphone_normal.png',
            background_down = 'assets/microphone_down.png'
        )
        self._recordBtn.bind(on_press = lambda x : self.start_record())
        self._recordBtn.bind(on_release = lambda x : self.stop_record())
        self.add_widget(self._recordBtn)
        
        self._glowIntensity = 0.75
        self._recordGlow = Image(
            source = 'assets/microphone_glow.png',
            size_hint = (None, 0.3 * self._glowIntensity),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3}
        )
        self.add_widget(self._recordGlow)
        
        Window.minimum_height = 320
        Window.minimum_width = 640
        
        Window.bind(on_resize = self.on_resize)
        Window.bind(on_rotate = self.on_rotate)
        Window.bind(on_show = self.on_show)
        Window.bind(on_maximize = self.on_maximize)
        Window.bind(on_restore = self.on_restore)
        
        
    def start_record(self):
        pass
    
    def stop_record(self):
        pass
    
    def update(self, window):
        self._recordBtn.size_hint_x = self._recordBtn.height / window.width
        self._recordGlow.size_hint_x = self._recordGlow.height / window.width
    
    def on_resize(self, window, width, height):
        self.update(window)
        
    def on_rotate(self, window):
        self.update(window)
        
    def on_show(self, window):
        self.update(window)
        
    def on_maximize(self, window):
        self.update(window)
        
    def on_restore(self, window):
        self.update(window)
        
class RecorderApp(App):

    def build(self):
        self.layout = MainLayout()
        return self.layout
    
if __name__ == '__main__':
    RecorderApp().run()