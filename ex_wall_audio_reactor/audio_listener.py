from pyaudio import PyAudio, paInt16
import numpy as np
import wave
from threading import Thread
from time import sleep, perf_counter
import logging

class AudioListener:

    RATE = 16000                            # The other mic works at 44100
    CHUNK = 1024                            # RATE / number of updates per second
    BLACKMAN_WINDOW = np.blackman(CHUNK)    # Decaying window on either side of chunk

    HIGH_THRESH_MAX = 0.7e6
    LOW_THRESH_MAX = 0.05e6

    MOVING_WINDOW_SIZE = 2

    def __init__(self):
        self.logger = logging.getLogger("AudioListener")
        self.py_audio = PyAudio()
        self.current_index = 0
        self.moving_window = [0] * self.MOVING_WINDOW_SIZE
        self.stream = self.py_audio.open(
            format=paInt16,
            channels=1,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK, 
            input_device_index=4
        )
        self.thread = Thread(target=self._thread)
        self.running = True
        self.thread.start()
        pass

    def _thread(self):
        while self.running:
            start_time = perf_counter()
            fft = self.get_fft_data()
            sense_range = sum(fft)
            self.moving_window[self.current_index] = sense_range.max()
            self.current_index = (self.current_index + 1) % self.MOVING_WINDOW_SIZE
            # self.logger.debug(f"FFT Duration: {perf_counter() - start_time:.2f}")

    def print_channel_info(self):
        for i in range(self.py_audio.get_device_count()):
            dev = self.py_audio.get_device_info_by_index(i)
            self.logger.debug((i,dev['name'],dev['maxInputChannels']))

    def close(self):
        self.running = False
        self.thread.join()
        self.stream.close()

    def get_fft_data(self):
        data = self.stream.read(self.CHUNK, exception_on_overflow=False)
        waveData = wave.struct.unpack("%dh"%(self.CHUNK), data)
        npArrayData = np.array(waveData)
        indata = npArrayData*self.BLACKMAN_WINDOW

        fft_data=np.abs(np.fft.rfft(indata))
        return np.log(fft_data).astype(int)
    

def main():
    listener = AudioListener()
    
    while True:
        print(f"{max(listener.moving_window)}")
        sleep(0.1)
    x = 1


if __name__ == "__main__":
    main()

