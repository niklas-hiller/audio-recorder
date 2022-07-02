import random
from time import sleep
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock

class MainLayout(FloatLayout):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._background = Image(
            source = 'assets/background.jpg',
            size_hint = (1.0, 1.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self._background)

        self._recordText = Label(
            text = "Maschinelles Lernen ist ein Oberbegriff für die „künstliche“ Generierung von Wissen aus Erfahrung: "
                + "Ein künstliches System lernt aus Beispielen und kann diese nach Beendigung der Lernphase verallgemeinern. "
                + "Dazu bauen Algorithmen beim maschinellen Lernen ein statistisches Modell auf, das auf Trainingsdaten beruht "
                + "und welches gegen die Testdaten getestet wird. Das heißt, es werden nicht einfach die Beispiele auswendig gelernt "
                + "(siehe Überanpassung), sondern Muster und Gesetzmäßigkeiten in den Lerndaten erkannt.",
            size = (0.9 * Window.width, 0.6 * Window.height),
            text_size = (0.9 * Window.width, 0.6 * Window.height),
            size_hint = (None, None),
            halign = 'center',
            valign = 'middle',
            pos_hint = {'center_x': 0.5, 'top': 0.95},
            font_size = Window.height * 0.6 * 0.05,
            color = (0.05, 0.05, 0.05, 0.85)
        )
        self.add_widget(self._recordText)

        self._recordBtn = Button(
            size_hint = (None, 0.3),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/microphone_normal.png',
            background_down = 'assets/microphone_down.png'
        )
        self._recordBtn.bind(on_press = lambda x : self.start_record())
        self._recordBtn.bind(on_release = lambda x : self.stop_record())
        
        self.glowEvent = None
        self.currentGlow = 1.0
        self.targetGlow = 1.0
        Clock.schedule_interval(self.update_intensity, 0.0)
        self._recordGlow = Image(
            source = 'assets/microphone_glow.png',
            size_hint = (None, 0.25 * self.currentGlow),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3}
        )
        self.add_widget(self._recordGlow)
        self.add_widget(self._recordBtn)
        
        Window.minimum_height = 320
        Window.minimum_width = 640
        
        Window.bind(on_resize = self.on_resize)
        Window.bind(on_rotate = self.on_rotate)
        Window.bind(on_show = self.on_show)
        Window.bind(on_maximize = self.on_maximize)
        Window.bind(on_restore = self.on_restore)
        
    def update_intensity(self, dt):
        if abs(self.targetGlow - self.currentGlow) < 0.03:
            self.currentGlow = self.targetGlow
        elif self.targetGlow < self.currentGlow:
            self.currentGlow -= 0.03
        elif self.targetGlow > self.currentGlow:
            self.currentGlow += 0.03
        
        self._recordGlow.size_hint_y = 0.25 * self.currentGlow
        self._recordGlow.size_hint_x = (0.25 * self.currentGlow * Window.height) / Window.width
        
    def simulate_audio(self):
        self.targetGlow = random.randint(100, 200) / 100
        
    def start_record(self):
        self.glowEvent = Clock.schedule_interval(lambda x : self.simulate_audio(), 0.1)
    
    def stop_record(self):
        Clock.unschedule(self.glowEvent)
        self.glowEvent = None
        self.targetGlow = 1.0
    
    def update(self, window):
        # Refresh button for recording
        self._recordBtn.size_hint_x = self._recordBtn.height / window.width
        
        # Refresh glow effect that indicates volume
        self._recordGlow.size_hint_x = self._recordGlow.height / window.width
        
        # Refresh Text to be recorded
        self._recordText.size = (0.9 * window.width, 0.6 * window.height)
        self._recordText.text_size = self._recordText.size
        self._recordText.font_size = (self._recordText.height * 0.05)

        # Refresh Background
        new_size_x = (window.height * self._background.image_ratio) / window.width
        new_size_y = (window.width * self._background.image_ratio) / window.height
        if new_size_x < 1.0:
            self._background.size_hint_x = 1.0
            self._background.size_hint_y = new_size_y
        else:
            self._background.size_hint_x = new_size_x
            self._background.size_hint_y = 1.0
    
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