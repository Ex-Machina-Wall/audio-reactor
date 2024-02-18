import numpy as np
from raspberry_pi_controller.constants import HEIGHT, WIDTH, MAPPING, NUM_PIXELS
from typing import List


class Frame:
    def __init__(self, pixel_array: np.array):
        self.pixel_array = np.clip((pixel_array).astype(int), 0, 255)

    def get_string_data(self) -> list: 
        pixels = [(0, 0, 0) for _ in range(NUM_PIXELS)]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if MAPPING[y][x] is not None:
                    pixel = self.pixel_array[y, x]
                    pixel_number = MAPPING[y][x]
                    pixels[pixel_number] = pixel[:3]
        return pixels

class Frames:
    def __init__(self, frames: List[Frame]):
        self.frames = frames
        self.frame = Frame(pixel_array=self.get_sum_frame())
        self.pixel_array = self.frame.pixel_array
    
    def get_sum_frame(self) -> np.array:
        sum_frame = None
        for frame in self.frames:
            if sum_frame is None:
                sum_frame = frame.pixel_array
            else:
                sum_frame = sum_frame + frame.pixel_array
        return sum_frame
        # return np.clip((sum_frame).astype(int), 0, 255)

    def get_string_data(self) -> list:
        return self.sum_frame.get_string_data()