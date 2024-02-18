from raspberry_pi_controller.effects.abstract_effect import Effect
from raspberry_pi_controller.constants import WIDTH, HEIGHT
from raspberry_pi_controller.frame import Frame
import numpy as np


class TwoColorRandom(Effect):
    FRAME_TIME = 0.1

    def __init__(self) -> None:
        super().__init__()
        self.accepted_commands = {
            "SET_PRIMARY_COLOR": self.set_primary_color,
            "SET_SECONDARY_COLOR": self.set_secondary_color,
            "SET_PRIMARY_BRIGHTNESS": self.set_primary_brightness,
            "SET_SECONDARY_BRIGHTNESS": self.set_secondary_brightness
        }
        self.primary_color = (0, 0, 20)
        self.secondary_color = (0, 0, 0)
        self.primary_brightness = 100
        self.secondary_brightness = 100

    @property
    def primary_color_scaled(self) -> tuple:
        scaled = (
            int(self.primary_color[0]*self.primary_brightness/100), 
            int(self.primary_color[1]*self.primary_brightness/100),
            int(self.primary_color[2]*self.primary_brightness/100)
            )
        return scaled
    
    @property
    def secondary_color_scaled(self) -> tuple:
        scaled = (
            int(self.secondary_color[0]*self.secondary_brightness/100), 
            int(self.secondary_color[1]*self.secondary_brightness/100),
            int(self.secondary_color[2]*self.secondary_brightness/100)
            )
        return scaled

    def set_primary_brightness(self, command: str):
        try:
            split_command = command.split("-")
            self.primary_brightness = int(split_command[1])
            self.logger.debug(f"Primary Brightness Set: {self.primary_brightness}")
        except Exception as e:
            self.logger.error(e)
            self.primary_brightness = 100

    def set_secondary_brightness(self, command: str):
        try:
            split_command = command.split("-")
            self.secondary_brightness = int(split_command[1])
            self.logger.debug(f"Secondary Brightness Set: {self.secondary_brightness}")
        except Exception as e:
            self.logger.error(e)
            self.primary_brightness = 100

    def set_primary_color(self, command: str):
        try:
            split_command = command.split('-')
            r = int(split_command[1])
            g = int(split_command[2])
            b = int(split_command[3])
            self.primary_color = (r, g, b)
            self.logger.debug(f"Primary Color Set: {self.primary_color}")
        except Exception as e:
            self.logger.error(e)
            self.primary_color = (0, 0, 0)
    
    def set_secondary_color(self, command: str):
        try:
            split_command = command.split('-')
            r = int(split_command[1])
            g = int(split_command[2])
            b = int(split_command[3])
            self.secondary_color = (r, g, b)
            self.logger.debug(f"Secondary Color Set: {self.secondary_color}")
        except Exception as e:
            self.logger.error(e)
            self.secondary_color = (0, 0, 0)
    
    def get_frame(self) -> Frame:
        frame = Frame(np.array([[self.primary_color_scaled for _ in range(WIDTH)] for _ in range(HEIGHT)]))
        return frame
