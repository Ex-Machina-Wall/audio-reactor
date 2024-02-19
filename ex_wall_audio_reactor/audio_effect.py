import time

from ex_wall_frame_transmitter.constants import WIDTH, HEIGHT
from ex_wall_audio_reactor.audio_tools.stream_analyzer import StreamAnalyzer
import numpy as np
from math import sqrt


class AudioEffect:

    def __init__(self, device: int = None):
        super().__init__()
        self.np_frame = np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])
        self.stream_analyzer = StreamAnalyzer(device=device)

        self.secondary_color = (0, 0, 255)
        self.brightness = 100
        self.primary_color = (255, 0, 0)

        self.high_frequency_react_state = True
        self.low_frequency_react_state = True
        if self.stream_analyzer.using_py_audio:
            # Py audio seems to decode the audio into much larger numbers
            self.high_frequency_threshold = 170000
            self.low_frequency_threshold = 300000
        else:
            self.high_frequency_threshold = 10  # 170000
            self.low_frequency_threshold = 30  # 300000

    @property
    def primary_color_scaled(self) -> tuple:
        scaled = (
            int(self.primary_color[0] * self.brightness / 100),
            int(self.primary_color[1] * self.brightness / 100),
            int(self.primary_color[2] * self.brightness / 100)
        )
        return scaled

    @property
    def secondary_color_scaled(self) -> tuple:
        scaled = (
            int(self.secondary_color[0] * self.brightness / 100),
            int(self.secondary_color[1] * self.brightness / 100),
            int(self.secondary_color[2] * self.brightness / 100)
        )
        return scaled

    """ Incoming command Handlers """

    def get_frame(self, current_frame: np.array = None) -> np.array:
        current_frame = np.zeros((HEIGHT, WIDTH, 3)) if current_frame is None else current_frame

        _, _, _, amplitudes = self.stream_analyzer.get_audio_features()
        # print(max(amplitudes))
        current_frame = self.get_perimeter_pulse(current_frame, amplitudes)

        current_frame = self.add_bass_pulse(current_frame, amplitudes)
        return current_frame

    def get_perimeter_pulse(self, current_frame, amplitudes) -> np.array:
        if not self.high_frequency_react_state:
            return current_frame

        max_height = 7
        middle_point_x = 8
        for y in range(HEIGHT):
            for x in range(WIDTH):
                frame_color = self.secondary_color_scaled

                # We are in the top half need top down section
                if y <= max_height:
                    if x <= middle_point_x:
                        amplitude = amplitudes[-x]
                    else:
                        amplitude = amplitudes[int(-middle_point_x + (-middle_point_x + x))]
                    height = round(min(amplitude / self.high_frequency_threshold, 1) * max_height + 0.5)
                    if y < height:
                        current_frame[y][x] = frame_color
                # We are on the bottom half section
                else:
                    if x <= middle_point_x:
                        amplitude = amplitudes[-x]
                    else:
                        amplitude = amplitudes[int(-middle_point_x + (-middle_point_x + x))]
                    height = round(min(amplitude / self.high_frequency_threshold, 1) * max_height + 0.5)
                    if (HEIGHT - y - 1) < height:
                        current_frame[y][x] = frame_color

        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return current_frame

    def add_bass_pulse(self, current_frame, amplitudes):
        if not self.low_frequency_react_state:
            return current_frame
        max_height = 4

        amplitude = sum(amplitudes[:3]) / len(amplitudes[:3])
        target_radius = round(min(amplitude / self.low_frequency_threshold, 1) * max_height)

        # Start drawing the circles
        y_offset = 6
        x_offset = 8
        for y in range(HEIGHT):
            _y = y - y_offset
            for x in range(WIDTH):
                _x = x - x_offset
                frame_color = self.primary_color_scaled
                # frame_color = current_frame[y][x]
                # _x and _y are the corrected x, y so that we iterate around the center of the wall
                # Calculate the distance the current pixel we're setting is from the center of the screen
                distance = sqrt(abs(_x * 2.3) + _y ** 2)
                if distance < target_radius:
                    # Draw the color in that location
                    current_frame[y][x] = frame_color

        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return current_frame
