from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation, AnimationTransition
from kivy.uix.slider import Slider

import hashlib
import json
import pyaudio
import numpy as np

def rms(arr):
    """ calculates the rms power of an array """
    return np.sqrt(np.mean(np.power(arr, 2)))

def dB(rms): 
    """ calculates the logarithmic dB value of a rms """
    return 20 * np.log10(rms)



# For Data Visualization (remove later)
[
    [
        "filename",
        [
            [
                # chunk 1
            ],
            [
                # chunk 2
            ],
            [
                # chunk n
            ]
        ]
    ],
    [
        "filename",
        [
            [
                # chunk 1
            ],
            [
                # chunk 2
            ],
            [
                # chunk n
            ]
        ]
    ]
]

class AudioStream:
    
    def __init__(self):
        self._chunks = []
        
    @property
    def chunks(self) -> list[list[bytes]]:
        return self._chunks
    
    def length(self):
        return len(self.chunks)
    
    def __getitem__(self, index : int) -> list[bytes]:
        return self.chunks[index]
    
    def append(self, chunk : list[bytes]):
        self.chunks.append(chunk)

    def to_numpy(self) -> np.ndarray:
        return np.array([np.frombuffer(chunk, dtype = np.float32) for chunk in self.chunks], dtype = np.float32)

    def to_numpyConcat(self) -> np.ndarray:
        return np.concatenate([chunk for chunk in self.to_numpy()])


class NO_MORE_TEXT(Exception):
    pass

class Data:
    
    def __init__(self, src = 'texts.json'):
        self._current = -1
        with open(src, encoding='utf-8') as f:
            self._texts = json.load(f)
        self._data = [None] * len(self._texts)
        
    @property
    def current(self) -> str:
        return self._texts[self._current]
        
    def next(self):
        if self._current + 1 >= len(self._texts): raise NO_MORE_TEXT
        self._current += 1
        return self._texts[self._current]
    
    def insert(self, data : AudioStream):
        _data = data.to_numpy()
        _hash = hashlib.md5(self.current.encode(encoding = 'utf-8')).digest()
        self._data[self._current] = np.array([_hash, _data])
        # Size of each chunk
        # print(f"Size {[chunk.size for chunk in data]}")
        # Equivalent to data.size
        # print(f"SizeTotal {np.sum([chunk.size for chunk in data])}")
        print(f"Recorded samples: {_data.size}")
        # Combine all chunks to one array
        # concat = np.concatenate([chunk for chunk in data])
        
        
    def to_csv(self):
        data = np.array(self._data)
        print(data)
        np.savetxt("data.csv", data, delimiter = ",")

class MainLayout(FloatLayout):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._data = None
        
        self._background = Image(
            source = 'assets/background.jpg',
            size_hint = (1.0, 1.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self._background)

        self._recordText = Label(
            text = "",
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
            max = 1.0,
            step = 1
        )
        self._playBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'right': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/play_normal.png',
            background_down = 'assets/play_down.png',
            background_disabled_normal = 'assets/play_normal.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._playBtn.bind(on_release = lambda x : self.play_audio())
        self._playing = False
        self._confirmBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/confirm_normal.png',
            background_down = 'assets/confirm_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._confirmBtn.bind(on_release = lambda x : self.save_audio())
        self._cancelBtn = Button(
            size_hint = (0.0, 0.0),
            pos_hint = {'center_x': 0.5, 'center_y': 0.3},
            always_release = True,
            background_normal = 'assets/cancel_normal.png',
            background_down = 'assets/cancel_down.png',
            opacity = 0.,
            border = (0, 0, 0, 0)
        )
        self._cancelBtn.bind(on_release = lambda x : self.delete_audio())
        
        self.add_widget(self._progressSlider)
        self.add_widget(self._playBtn)
        self.add_widget(self._confirmBtn)
        self.add_widget(self._cancelBtn)
        
        Window.minimum_height = 320
        Window.minimum_width = 640
        
        Window.bind(on_resize = self.on_resize)
        Window.bind(on_rotate = self.on_rotate)
        Window.bind(on_show = self.on_show)
        Window.bind(on_maximize = self.on_maximize)
        Window.bind(on_restore = self.on_restore)
        
        Clock.schedule_once(lambda x : self.update(), 0.1)
        
        self.update_text()
        
    def show_new_text(self):
        try:
            self._recordText.text = self._data.next()
        except NO_MORE_TEXT as e:
            self._recordText.text = "Done"
            self._data.to_csv()
        anim = Animation(opacity = 1.0)
        anim.start(self._recordText)
        
    def update_text(self):
        if self._data is None:
            self._data = Data()
        anim = Animation(opacity = 0.0)
        anim.bind(on_complete = lambda x, y : self.show_new_text())
        anim.start(self._recordText)

        
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
        
    def process_audio_input(self, in_data, frame_count, time_info, flag):
        self.audioStream.append(in_data)
        audio_data = np.frombuffer(in_data, dtype = np.float32)
        
        db = float(dB(rms(audio_data)))
        self.minimum_db = db if db < self.minimum_db else self.minimum_db
        self.maximum_db = db if db > self.maximum_db else self.maximum_db
        
        if (self.maximum_db - self.minimum_db) != 0:
            normalized = round((db - self.minimum_db) / (self.maximum_db - self.minimum_db), 2)
            self.targetGlow = normalized + 1.0
        
        return in_data, pyaudio.paContinue
    
    def process_audio_output(self, in_data, frame_count, time_info, flag):
        c = int(self._progressSlider.value)
        if c + 1 < self.audioStream.length():
            self._progressSlider.value += 1
            return self.audioStream[c], pyaudio.paContinue
        else:
            self._progressSlider.value += 1
            self._playBtn.background_normal = 'assets/play_normal.png'
            self._playBtn.background_down = 'assets/play_down.png'
            self._playing = False
            return self.audioStream[c], pyaudio.paComplete
        
    def show_recordBtn(self, animation, widget):
        self.finishedAnim += 1
        if self.finishedAnim >= 4:
            anim = Animation(size_hint = ((0.3 * Window.height ) / Window.width, 0.3),
                             opacity = 1.0,
                             duration = 0.5, transition = AnimationTransition.in_out_sine)
            anim.start(self._recordBtn)
        
    def hide_audio_ui(self):
        if self._playing:
            self._playing = False
            self._playBtn.background_normal = 'assets/play_normal.png'
            self._playBtn.background_down = 'assets/play_down.png'
            self.stream.stop_stream()
            self.stream.close()
            self.pyaudio.terminate()
        anim1 = Animation(size_hint = (0.0, 0.0),
                          opacity = 0.0,
                          pos_hint = {'center_x': 0.5, 'center_y': 0.3},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim2 = Animation(size_hint = (0.0, 0.0),
                          opacity = 0.0,
                          pos_hint = {'center_x': 0.5, 'center_y': 0.3},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim3 = Animation(size_hint = (0.0, 0.0),
                          opacity = 0.0,
                          pos_hint = {'center_x': 0.5, 'center_y': 0.3},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        anim4 = Animation(size_hint = (0.0, 0.0),
                          opacity = 0.0,
                          pos_hint = {'right': 0.5, 'center_y': 0.3},
                          duration = 0.5, transition = AnimationTransition.in_out_sine)
        self.finishedAnim = 0
        anim1.bind(on_complete = self.show_recordBtn)
        anim2.bind(on_complete = self.show_recordBtn)
        anim3.bind(on_complete = self.show_recordBtn)
        anim4.bind(on_complete = self.show_recordBtn)
        
        anim1.start(self._cancelBtn)
        anim2.start(self._confirmBtn)
        anim3.start(self._progressSlider)
        anim4.start(self._playBtn)
        
    def save_audio(self):
        self._data.insert(self.audioStream)
        self.hide_audio_ui()
        self.update_text()
        
    def delete_audio(self):
        self.hide_audio_ui()
        
        
    def play_audio(self):
        self._playing = not self._playing
        if self._playing:
            if self._progressSlider.value >= self.audioStream.length():
                self._progressSlider.value = 0
            self._playBtn.background_normal = 'assets/pause_normal.png'
            self._playBtn.background_down = 'assets/pause_down.png'
            self.pyaudio = pyaudio.PyAudio()
            sample_rate = int(self.pyaudio.get_default_output_device_info()['defaultSampleRate'])
            device = self.pyaudio.get_default_output_device_info()['index']
            self.stream = self.pyaudio.open(format = pyaudio.paFloat32,
                                            output_device_index = device,
                                            channels = 1,
                                            rate = sample_rate,
                                            output = True,
                                            input = False,
                                            stream_callback = self.process_audio_output)
        else:
            self._playBtn.background_normal = 'assets/play_normal.png'
            self._playBtn.background_down = 'assets/play_down.png'
            self.stream.stop_stream()
            self.stream.close()
            self.pyaudio.terminate()
        
        
    def start_record(self):
        # self.glowEvent = Clock.schedule_interval(lambda x : self.simulate_audio(), 0.1)
        self.minimum_db =  10000    # just some high value
        self.maximum_db = -10000    # just some small value
        self.audioStream = AudioStream()
        
        self.pyaudio = pyaudio.PyAudio()
        # sample_rate / 1024 = chunks per second
        sample_rate = int(self.pyaudio.get_default_input_device_info()['defaultSampleRate'])
        print(f"Recording with {sample_rate}Hz")
        device = self.pyaudio.get_default_input_device_info()['index']
        self.stream = self.pyaudio.open(format = pyaudio.paFloat32,
                                        input_device_index = device,
                                        channels = 1,
                                        rate = sample_rate,
                                        output = False,
                                        input = True,
                                        stream_callback = self.process_audio_input)
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
        anim1.start(self._cancelBtn)
        anim2.start(self._confirmBtn)
        anim3.start(self._progressSlider)
        anim4.start(self._playBtn)
    
    def stop_record(self):        
        # Clock.unschedule(self.glowEvent)
        # self.glowEvent = None
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        
        self._progressSlider.max = self.audioStream.length() - 1
        self._progressSlider.value = 0
        
        self.targetGlow = 1.0
        anim = Animation(size_hint = (0.0, 0.0), duration = 0.5, opacity = 0.0, transition = AnimationTransition.in_out_sine)
        anim.bind(on_complete = self.hide_recordBtn)
        anim.start(self._recordBtn)
    
    def update(self):
        # Refresh button for recording
        self._recordBtn.size_hint_x = self._recordBtn.height / Window.width
        # Refresh button for confirm
        self._confirmBtn.size_hint_x = self._confirmBtn.height / Window.width
        # Refresh button for cancel
        self._cancelBtn.size_hint_x = self._cancelBtn.height / Window.width
        # Refresh button for play
        self._playBtn.size_hint_x = self._playBtn.height / Window.width
        
        # Refresh Text to be recorded
        self._recordText.size = (0.9 * Window.width, 0.6 * Window.height)
        self._recordText.text_size = self._recordText.size
        self._recordText.font_size = (self._recordText.height * 0.05)

        # Refresh Background
        new_size_x = (Window.height * self._background.image_ratio) / Window.width
        new_size_y = (Window.width * self._background.image_ratio) / Window.height
        if new_size_x < 1.0:
            self._background.size_hint_x = 1.0
            self._background.size_hint_y = new_size_y
        else:
            self._background.size_hint_x = new_size_x
            self._background.size_hint_y = 1.0
    
    def on_resize(self, window, width, height):
        self.update()
        
    def on_rotate(self, window):
        self.update()
        
    def on_show(self, window):
        self.update()
        
    def on_maximize(self, window):
        self.update()
        
    def on_restore(self, window):
        self.update()
        
class RecorderApp(App):

    def build(self):
        self.layout = MainLayout()
        return self.layout
    
if __name__ == '__main__':
    RecorderApp().run()