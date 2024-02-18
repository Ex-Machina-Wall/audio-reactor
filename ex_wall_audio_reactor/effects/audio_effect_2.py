from raspberry_pi_controller.constants import WIDTH, HEIGHT, complement
from raspberry_pi_controller.frame import Frame
from raspberry_pi_controller.constants import complement, convert_incoming_color
from raspberry_pi_controller.audio_reactor.stream_analyzer import Stream_Analyzer
from raspberry_pi_controller.effects.abstract_effect import Effect
import numpy as np
from math import sqrt
from time import perf_counter

class AudioEffect2(Effect):
    PEAK_AMPLITUDE = 170000
    PEAK_BASS_AMPLITUDE = 300000

    def __init__(self):
        super().__init__()
        self.accepted_commands = {
            "SET_HIGH_FREQUENCY_REACT_STATE": self.set_frequency_react_state,
            "SET_LOW_FREQUENCY_REACT_STATE": self.set_frequency_react_state,
            "SET_HIGH_FREQUENCY_THRESHOLD": self.set_freq_threshold,
            "SET_LOW_FREQUENCY_THRESHOLD": self.set_freq_threshold,
            # "SET_PRIMARY_COLOR": self.set_color,
            "SET_SECONDARY_COLOR": self.set_color,
            "SET_SECONDARY_BRIGHTNESS": self.set_brightness
        }
        self.np_frame = np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])
        self.stream_analyzer = Stream_Analyzer()
        
        self.secondary_color = (0, 0, 255)
        self.brightness = 100
        self.primary_color = (255, 0, 0)

        self.high_frequency_react_state = True
        self.low_frequency_react_state = True
        self.high_frequency_threshold = 170000
        self.low_frequency_threshold = 300000

    @property
    def primary_color_scaled(self) -> tuple:
        scaled = (
            int(self.primary_color[0]*self.brightness/100), 
            int(self.primary_color[1]*self.brightness/100),
            int(self.primary_color[2]*self.brightness/100)
            )
        return scaled
    
    @property
    def secondary_color_scaled(self) -> tuple:
        scaled = (
            int(self.secondary_color[0]*self.brightness/100), 
            int(self.secondary_color[1]*self.brightness/100),
            int(self.secondary_color[2]*self.brightness/100)
            )
        return scaled

    """ Incoming command Handlers """

    def set_freq_threshold(self, command: str):
        variable_mapping = {
            "SET_HIGH_FREQUENCY_THRESHOLD": "high_frequency_threshold",
            "SET_LOW_FREQUENCY_THRESHOLD": "low_frequency_threshold"
        }
        try:
            thresh_type, value = command.split("-")
            value = int(value)
            setattr(self, variable_mapping[thresh_type], value)
            self.logger.info(f"Set {variable_mapping[thresh_type]} to {value}")
        except Exception as e:
            self.logger.error(e)
            self.high_frequency_threshold = 170000
            self.low_frequency_threshold = 300000

    def set_brightness(self, command: str):
        try:
            split_command = command.split("-")
            self.brightness = int(split_command[1])
            self.logger.info(f"React Brightness Set: {self.brightness}")
        except Exception as e:
            self.logger.error(e)
            self.brightness = 100

    def set_frequency_react_state(self, command: str):
        variable_mapping = {
            "SET_HIGH_FREQUENCY_REACT_STATE": "high_frequency_react_state",
            "SET_LOW_FREQUENCY_REACT_STATE": "low_frequency_react_state"
        }
        try:
            thresh_type, state = command.split("-")
            state = state == "ON"
            setattr(self, variable_mapping[thresh_type], state)
            self.logger.info(f"Set {variable_mapping[thresh_type]} to {state}")
        except Exception as e:
            self.logger.error(e)
            self.high_frequency_react_state = False
            self.low_frequency_react_state = False

    def set_color(self, command: str):
        variable_mapping = {
            "SET_PRIMARY_COLOR": "primary_color",
            "SET_SECONDARY_COLOR": "primary_color"
        }
        try:
            command, r, g, b = command.split('-')
            r, g, b = convert_incoming_color(r, g, b)
            setattr(self, variable_mapping[command], (r, g, b))
            self.logger.info(f"{variable_mapping[command]}: {(r, g, b)}")
        except Exception as e:
            self.logger.error(e)
            self.secondary_color = (0, 0, 255)
            self.primary_color = (255, 0, 0)
        
        # May want to remove this
        self.secondary_color = complement(*self.primary_color)

    def get_frame(self, current_frame: np.array = None) -> Frame:
        start_time = perf_counter()
        current_frame = current_frame if current_frame is not None else np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])

        _, _, _, amplitudes = self.stream_analyzer.get_audio_features()

        current_frame = self.get_perimeter_pulse(current_frame, amplitudes)

        current_frame = self.add_bass_pulse(current_frame, amplitudes)
        end_time = perf_counter()
        # self.logger.debug(f"Audio frame generation duration: {end_time-start_time:.2f}s")
        return Frame(current_frame)
    
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
                    height = round(min(amplitude/self.high_frequency_threshold, 1) * max_height + 0.5)
                    if y < height:
                        current_frame[y][x] = frame_color
                # We are on the bottom half section
                else:  
                    if x <= middle_point_x:
                        amplitude = amplitudes[-x]
                    else:
                        amplitude = amplitudes[int(-middle_point_x + (-middle_point_x + x))]
                    height = round(min(amplitude/self.high_frequency_threshold, 1) * max_height + 0.5)
                    if (HEIGHT - y - 1) < height:
                        current_frame[y][x] = frame_color

        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return current_frame

    def add_bass_pulse(self, current_frame, amplitudes):
        if not self.low_frequency_react_state:
            return current_frame
        max_height = 4

        amplitude = sum(amplitudes[:3])/len(amplitudes[:3])
        target_radius = round(min(amplitude/self.low_frequency_threshold, 1) * max_height)
        
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
                distance = sqrt(abs(_x*2.3) + _y**2)
                if distance < target_radius:
                    # Draw the color in that location
                    current_frame[y][x] = frame_color

        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return current_frame

    # def get_frame(self) -> Frame:
    #     """
    #     This is the standard get frame, it just adds a fixed color, which can be set by secondary color
    #     """
    #     # Get the start time of the function for debugging purposes
    #     _, _, bins, amplitude = self.stream_analyzer.get_audio_features()
    #     self.np_frame = np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])

    #     for y in range(HEIGHT):
    #         for x in range(WIDTH):
    #             y_max = int(min(amplitude[x]/200000, 1)*HEIGHT + 0.5)
    #             if y <= y_max:
    #                 self.np_frame[HEIGHT - y - 1][x] = (255, 0 ,0)
    #     # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
    #     return Frame(self.np_frame)
