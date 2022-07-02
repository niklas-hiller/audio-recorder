import random

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation, AnimationTransition
from kivy.uix.slider import Slider

import pyaudio
import numpy as np

def rms(arr):
    """ calculates the rms power of an array """
    return np.sqrt(np.mean(np.power(arr, 2)))

def dB(rms): 
    """ calculates the logarithmic dB value of a rms """
    return 20 * np.log10(rms)

class MainLayout(FloatLayout):
    
    INTENSITY_DECIBEL_RANGE = (20, 100)
    
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
            background_down = 'assets/microphone_down.png',
            background_disabled_normal = 'assets/microphone_normal.png',
            border = (0, 0, 0, 0)
        )
        self._recordBtn.bind(on_press = lambda x : self.start_record())
        self._recordBtn.bind(on_release = lambda x : self.stop_record())
        
        self.glowEvent = None
        self.currentGlow = 1.0
        self.targetGlow = 1.0
        Clock.schedule_interval(self.update_intensity, 0.0)
        self._recordGlow = Image(
            source = 'assets/microphone_glow.png',
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3}
        )
        self.add_widget(self._recordGlow)
        self.add_widget(self._recordBtn)
        
        
        self._progressSlider = Slider(
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            value = 0.,
            opacity = 0.,
            max = 1.0
        )
        self._playBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'right': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/play_normal.png',
            background_down = 'assets/play_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._pauseBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'right': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/play_normal.png',
            background_down = 'assets/play_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._confirmBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/confirm_normal.png',
            background_down = 'assets/confirm_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._cancelBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/cancel_normal.png',
            background_down = 'assets/cancel_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self.add_widget(self._progressSlider)
        self.add_widget(self._playBtn)
        self.add_widget(self._pauseBtn)
        self.add_widget(self._confirmBtn)
        self.add_widget(self._cancelBtn)
        
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
            
        if self.currentGlow == 1.0:
            self._recordGlow.opacity = 0.0
        else:
            self._recordGlow.opacity = 1.0
            
        self._recordGlow.size_hint_y = round(0.25 * self.currentGlow, 2)
        self._recordGlow.size_hint_x = round((0.25 * self.currentGlow * Window.height) / Window.width, 2)
        
    # def simulate_audio(self):
    #     self.targetGlow = random.randint(100, 200) / 100
        
    def process_audio(self, in_data, frame_count, time_info, flag):
        audio_data = np.fromstring(in_data, dtype = np.float32)
        
        db = float(dB(rms(audio_data)))
        self.minimum_db = db if db < self.minimum_db else self.minimum_db
        self.maximum_db = db if db > self.maximum_db else self.maximum_db
        
        if (self.maximum_db - self.minimum_db) != 0:
            normalized = round((db - self.minimum_db) / (self.maximum_db - self.minimum_db), 2)
            self.targetGlow = normalized + 1.0
        
        return in_data, pyaudio.paContinue
        
    def start_record(self):
        # self.glowEvent = Clock.schedule_interval(lambda x : self.simulate_audio(), 0.1)
        self.minimum_db =  10000    # just some high value
        self.maximum_db = -10000    # just some small value
        
        self.pyaudio = pyaudio.PyAudio()
        sample_rate = int(self.pyaudio.get_default_input_device_info()['defaultSampleRate'])
        device = self.pyaudio.get_default_input_device_info()['index']
        self.stream = self.pyaudio.open(format = pyaudio.paFloat32,
                                        input_device_index = device,
                                        channels = 1,
                                        rate = sample_rate,
                                        output = False,
                                        input = True,
                                        stream_callback = self.process_audio)
        self.stream.start_stream()
    
    def hide_recordBtn(self, animation, widget):
        widget.opacity = 0.0
        anim1 = Animation(size_hint = ((0.15 * Window.height) / Window.width, 0.15),
                          opacity = 1.0,
                          pos_hint = {'center_x': 0.3, 'center_y': 0.2},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim2 = Animation(size_hint = ((0.15 * Window.height) / Window.width, 0.15),
                          opacity = 1.0,
                          pos_hint = {'center_x': 0.7, 'center_y': 0.2},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim3 = Animation(size_hint = (0.5, 0.05),
                          opacity = 1.0,
                          pos_hint = {'center_x': 0.5, 'center_y': 0.35},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim4 = Animation(size_hint = ((0.05 * Window.height) / Window.width, 0.05),
                          opacity = 1.0,
                          pos_hint = {'right': 0.245, 'center_y': 0.35},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim5 = Animation(size_hint = ((0.05 * Window.height) / Window.width, 0.05),
                          opacity = 0.0,
                          pos_hint = {'right': 0.245, 'center_y': 0.35},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim1.start(self._cancelBtn)
        anim2.start(self._confirmBtn)
        anim3.start(self._progressSlider)
        anim4.start(self._playBtn)
        anim5.start(self._pauseBtn)
    
    def stop_record(self):
        # Clock.unschedule(self.glowEvent)
        # self.glowEvent = None
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        self.targetGlow = 1.0
        anim = Animation(size_hint = (0.0, 0.0), duration = 0.5, opacity = 0.0, transition = AnimationTransition.in_out_sine)
        anim.bind(on_complete = self.hide_recordBtn)
        anim.start(self._recordBtn)
    
    def update(self, window):
        # Refresh button for recording
        self._recordBtn.size_hint_x = self._recordBtn.height / window.width
        # Refresh button for confirm
        self._confirmBtn.size_hint_x = self._confirmBtn.height / window.width
        # Refresh button for cancel
        self._cancelBtn.size_hint_x = self._cancelBtn.height / window.width
        
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