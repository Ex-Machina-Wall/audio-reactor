from raspberry_pi_controller.constants import WIDTH, HEIGHT, complement
from raspberry_pi_controller.frame import Frame
from time import perf_counter
import numpy as np
from math import sqrt
from raspberry_pi_controller.audio_listener import AudioListener
from raspberry_pi_controller.constants import LoopBuffer
from raspberry_pi_controller.effects.abstract_effect import Effect


class AudioEffect(Effect):
    MIN_REACT_THRESHOLD = 11.3

    def __init__(self):
        super().__init__()
        self.accepted_commands = {
            "SET_SECONDARY_COLOR": self.set_secondary_color,
            "SET_SECONDARY_BRIGHTNESS": self.set_secondary_brightness

        }
        self.np_frame = np.array([[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)])
        
        self.circle_radii = list()
        self.listener = AudioListener()
        
        self.last_trigger_time = perf_counter()
        self.trigger_bpm_window = LoopBuffer(size=50, default_value=0.5)
        # Starting react level
        self.react_level = 11
        self.target_bps = 125/60
        self.threshold_adjust_gain = 0.0003
        self.secondary_brightness = 100
        self.secondary_color = (100, 0, 0)

    def set_secondary_color(self, command: str):
        try:
            split_command = command.split('-')
            r = int(split_command[1])
            g = int(split_command[2])
            b = int(split_command[3])
            self.secondary_color = (r, g, b)
            self.logger.debug(f"Secondary Color Set: {self.secondary_color}")
        except Exception as e:
            self.logger.debug(e)
            self.secondary_color = (0, 0, 0)

    def set_secondary_brightness(self, command: str):
        try:
            split_command = command.split("-")
            self.secondary_brightness = int(split_command[1])
            self.logger.debug(f"Audio React Brightness Set: {self.secondary_brightness}")
        except Exception as e:
            self.logger.debug(e)
            self.primary_brightness = 100

    def deal_with_dynamic_threshold(self):

        bps = 1/self.trigger_bpm_window.average()
        # This will be about 75% or something
        bps_percent_error = (bps - self.target_bps)/self.target_bps
        
        if self.trigger_bpm_window.variance() < 0.02:
            attenuation = 0.5
        else:
            attenuation = 1
        adjust_amount = self.react_level * (bps_percent_error * self.threshold_adjust_gain) * attenuation
        if self.react_level < self.MIN_REACT_THRESHOLD and adjust_amount < 0:
            # self.logger.debug(f"BPS {bps:.2f} | {self.react_level} too low to adjust")
            pass
        else:
            # self.logger.debug(f"BPS {bps:.2f} | {self.react_level} + {adjust_amount:.6f}")
            self.react_level = self.react_level + adjust_amount

    def get_frame(self) -> Frame:
        """
        This is the standard get frame, it just adds a fixed color, which can be set by secondary color
        """
        # Get the start time of the function for debugging purposes
        start_time = perf_counter()
        circle_movement_speed = 30
        # Check how loud the bass is now
        most_recent_audio_level = max(self.listener.moving_window)
        # self.logger.debug(f"Most recent Audio Level {most_recent_audio_level}")
        # self.logger.debug(f"Variance: {self.trigger_bpm_window.variance()}")
        # If the base is louder than our threshold level add another circle starting at the center
        # Target ranges is holding the radius' of each circle we need to draw
        # We start at -30 units because in the next interation we are adding 30 units
        if most_recent_audio_level > self.react_level: # 240000:
            # Save the time for BPM Calculation
            time_now = perf_counter()
            time_since_last_trigger = round(time_now - self.last_trigger_time, 4)
            self.last_trigger_time = time_now
            self.trigger_bpm_window.append(time_since_last_trigger)
            
            # Add the new circle
            if self.circle_radii and self.circle_radii[-1] == 0:
                # This means we JUST added one on the last frame
                # self.logger.debug(f"---------------------------- TRIGGERED (but skipped)")
                pass
            else:
                self.circle_radii.append(circle_movement_speed)
                # self.logger.debug(f"---------------------------- TRIGGERED")
        else:
            # Save the time for BPM Calculation
            # self.logger.debug(f"---------------------------- ")
            time_now = perf_counter()
            time_since_last_trigger = time_now - self.last_trigger_time
            self.trigger_bpm_window.append(time_since_last_trigger)
        
        self.deal_with_dynamic_threshold()
        
        # When a circle exceeds a radius of 500 we will remove it from the target_ranges list
        # pop list keeps track of the indexes to remove
        pop_list = list()
        for i in range(len(self.circle_radii)):
            # Increase the radious of each circle by 30 units ever iteration
            self.circle_radii[i] += circle_movement_speed
            # If any circle is over 500 units add it to the pop list
            if self.circle_radii[i] > 500:
                pop_list.append(i)

        # Remove the circles we no longer need
        pop_list.sort(reverse=True)
        for i in pop_list:
            self.circle_radii.pop(i)

        # Start drawing the circles
        y_offset = 6
        x_offset = 8
        # Devide the total brightness of the frame so the circles become less bright each iteration
        self.np_frame = self.np_frame/1.2

        for y in range(HEIGHT):
            _y = y - y_offset
            for x in range(WIDTH):
                _x = x - x_offset
                # _x and _y are the corrected x, y so that we iterate around the center of the wall
                # Calculate the distance the current pixel we're setting is from the center of the screen
                distance = sqrt(_x**2 + _y**2)*10
                # See what the closes circle is to this distance by calculating the minimun error
                all_distance_errors = [abs(target - distance) for target in self.circle_radii]
                if all_distance_errors:
                    distance_error = min(all_distance_errors)
                    # Draw the color in that location
                    self.np_frame[y][x] = (255 - (distance_error*3), 0, 0)
        
        end_time = perf_counter()
        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return Frame(self.np_frame)

    def get_frame_adjust(self, current_frame: np.array) -> Frame:
        """
        This is the standard get frame, it just adds a fixed color, which can be set by secondary color
        """
        # Get the start time of the function for debugging purposes
        start_time = perf_counter()
        circle_movement_speed = 3
        circle_thickness = 4
        # Check how loud the bass is now
        most_recent_audio_level = max(self.listener.moving_window)
        # self.logger.debug(f"Most recent Audio Level {most_recent_audio_level}")
        # self.logger.debug(f"Variance: {self.trigger_bpm_window.variance()}")
        
        # If the base is louder than our threshold level add another circle starting at the center
        # Target ranges is holding the radius' of each circle we need to draw
        # We start at -30 units because in the next interation we are adding 30 units
        if most_recent_audio_level > self.react_level: # 240000:
            # Save the time for BPM Calculation
            time_now = perf_counter()
            time_since_last_trigger = round(time_now - self.last_trigger_time, 4)
            self.last_trigger_time = time_now
            self.trigger_bpm_window.append(time_since_last_trigger)
            
            # Add the new circle
            if self.circle_radii and self.circle_radii[-1] == 0:
                # This means we JUST added one on the last frame
                # self.logger.debug(f"---------------------------- TRIGGERED (but skipped)")
                pass
            else:
                self.circle_radii.append(-circle_movement_speed)
                # self.logger.debug(f"---------------------------- TRIGGERED")
        else:
            # Save the time for BPM Calculation
            # self.logger.debug(f"---------------------------- ")
            time_now = perf_counter()
            time_since_last_trigger = time_now - self.last_trigger_time
            self.trigger_bpm_window.append(time_since_last_trigger)
        
        self.deal_with_dynamic_threshold()
        
        # When a circle exceeds a radius of 500 we will remove it from the target_ranges list
        # pop list keeps track of the indexes to remove
        pop_list = list()
        for i in range(len(self.circle_radii)):
            # Increase the radious of each circle by 30 units ever iteration
            self.circle_radii[i] += circle_movement_speed
            # If any circle is over 20 units add it to the pop list
            if self.circle_radii[i] > 20:
                pop_list.append(i)

        # Remove the circles we no longer need
        pop_list.sort(reverse=True)
        for i in pop_list:
            self.circle_radii.pop(i)

        # If the reacting is off don't finish the rest of the function
        if self.secondary_brightness < 50:
            return Frame(current_frame)

        # Start drawing the circles
        y_offset = 6
        x_offset = 8
        # Devide the total brightness of the frame so the circles become less bright each iteration
        # self.np_frame = self.np_frame/1.2

        for y in range(HEIGHT):
            _y = y - y_offset
            for x in range(WIDTH):
                _x = x - x_offset
                # _x and _y are the corrected x, y so that we iterate around the center of the wall
                # Calculate the distance the current pixel we're setting is from the center of the screen
                distance = sqrt(_x**2 + _y**2)
                # See what the closes circle is to this distance by calculating the minimun error
                all_distance_errors = [abs(target - distance) for target in self.circle_radii]
                if all_distance_errors:
                    distance_error = min(min(all_distance_errors), circle_thickness) / circle_thickness
                    orig_color_percent = distance_error
                    compliment_color_percent = 1 - distance_error
                    # Draw the color in that location
                    orig_color = current_frame[y][x]
                    compliment_color = complement(*orig_color)
                    self.logger.debug(compliment_color)
                    current_frame[y][x] = (orig_color[0]*orig_color_percent + compliment_color[0]*compliment_color_percent, 
                                           orig_color[1]*orig_color_percent + compliment_color[1]*compliment_color_percent, 
                                           orig_color[2]*orig_color_percent + compliment_color[2]*compliment_color_percent)
        
        end_time = perf_counter()
        # self.logger.debug(f"Duration {end_time-start_time:.4f}s")
        return Frame(current_frame)
