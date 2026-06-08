import time

from decouple import config
from ex_wall_frame_transmitter.constants import WIDTH, HEIGHT
from ex_wall_audio_reactor.audio_tools.stream_analyzer import StreamAnalyzer
import numpy as np
from math import sqrt


class AudioEffect:

    # Number of dB above each threshold at which the LED response saturates
    # (renders the full visual extent). Smaller value = "twitchier" response,
    # larger value = "smoother" response across the dynamic range.
    DYNAMIC_RANGE_DB = 15.0

    def __init__(self, device=None):
        super().__init__()
        if device is None:
            device = config("EX_WALL_AUDIO_INPUT", default="visualizer_sink.monitor")
        self.np_frame = np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])
        self.stream_analyzer = StreamAnalyzer(device=device)

        self.secondary_color = (0, 0, 255)
        self.brightness = 100
        self.primary_color = (255, 0, 0)

        # Thresholds are now in dBFS-like units (see stream_analyzer.DBFS_REFERENCE).
        # Same scale regardless of audio backend. Typical loud music peaks near 0 dBFS;
        # quiet passages around -30 dBFS. Defaults react on moderately loud audio.
        self.high_frequency_react_state = True
        self.low_frequency_react_state = True
        self.high_frequency_threshold = -30.0  # dBFS
        self.low_frequency_threshold = -28.0   # dBFS

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

    def _activation(self, amplitude_db, threshold_db):
        """Map a bin energy (dBFS) relative to its threshold to [0, 1].

        Returns 0 when amplitude is at or below threshold, 1 when amplitude
        is DYNAMIC_RANGE_DB or more above threshold, linear in between.
        """
        excess = amplitude_db - threshold_db
        return max(0.0, min(excess / self.DYNAMIC_RANGE_DB, 1.0))

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
                    height = round(self._activation(amplitude, self.high_frequency_threshold) * max_height + 0.5)
                    if y < height:
                        current_frame[y][x] = frame_color
                # We are on the bottom half section
                else:
                    if x <= middle_point_x:
                        amplitude = amplitudes[-x]
                    else:
                        amplitude = amplitudes[int(-middle_point_x + (-middle_point_x + x))]
                    height = round(self._activation(amplitude, self.high_frequency_threshold) * max_height + 0.5)
                    if (HEIGHT - y - 1) < height:
                        current_frame[y][x] = frame_color

        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return current_frame

    def add_bass_pulse(self, current_frame, amplitudes):
        if not self.low_frequency_react_state:
            return current_frame
        max_height = 4

        amplitude = sum(amplitudes[:3]) / len(amplitudes[:3])
        target_radius = round(self._activation(amplitude, self.low_frequency_threshold) * max_height)

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
