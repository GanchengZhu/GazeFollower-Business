# _*_ coding: utf-8 _*_
# Author: GC Zhu
# Email: zhugc2016@gmail.com

import math
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
# import pandas as pd
import pygame

from core import CalibrationPoint, CalibrationResult, TCCIDesktopET, GazeInfo


# from misc import GazeInfo


class Graphics:
    def __init__(self, et_library: TCCIDesktopET):
        """

        :param et_library:
        """
        # color constant
        self._color_white = (255, 255, 255)
        self._color_red = (255, 0, 0)
        self._color_black = (0, 0, 0)
        self._color_blue = (0, 0, 255)
        self._color_green = (0, 255, 0)

        # native library
        self.et_library = et_library

        # error bar attributes
        self.error_bar_color = (0, 255, 0)  # Green color for the error bar
        self.error_bar_thickness = 2  # Thickness of the error bar lin

        # initialize the font
        self.guidance_font = pygame.font.SysFont('Microsoft YaHei', 20, bold=True)

        # initialize the mixer and load sound
        pygame.mixer.init()
        _audio_path = Path(__file__).parent.absolute() / 'res/audio/beep.wav'
        self.feedback_sound = pygame.mixer.Sound(_audio_path)  # Replace with the path to your sound file

        self._new_session()

        self.screen_height = et_library.screen_height
        self.screen_width = et_library.screen_width

        self.image_width = self.et_library.image_width
        self.image_height = self.et_library.image_height
        self.pygame_previewer_size = (self.image_width, self.image_height)
        self.previewer_center = (self.screen_width / 2 - self.image_width / 2,
                                 self.screen_height / 2 - self.image_height / 2)
        self.previewer_surface = pygame.Surface(self.pygame_previewer_size)
        # Image size
        self.running = False
        self._last_drawing_point: CalibrationPoint = CalibrationPoint(0, 0)

    def generate_calibration_directions(self):
        num_points = len(self.calibration_points)
        # Generate lists for directions
        self.calibration_directions = ['left'] * (num_points // 2) + ['right'] * (num_points - num_points // 2)
        # Shuffle the list with a fixed seed for reproducibility
        np.random.seed(2024)
        np.random.shuffle(self.calibration_directions)

    def generate_validation_directions(self):
        num_points = len(self.validation_points)
        # Generate lists for directions
        self.validation_directions = ['left'] * (num_points // 2) + ['right'] * (num_points - num_points // 2)
        # Shuffle the list with a fixed seed for reproducibility
        np.random.seed(912)
        np.random.shuffle(self.validation_directions)

    def set_calibration_points(self, calibration_points):
        """

        :param calibration_points:
        :return:
        """
        self.calibration_points = [(int(x * self.screen_width), int(y * self.screen_height)) for x, y in
                                   calibration_points]
        self.generate_calibration_directions()

    def set_validation_points(self, validation_points):
        self.validation_points = [(int(x * self.screen_width), int(y * self.screen_height)) for x, y in
                                  validation_points]
        self.generate_validation_directions()

    def draw_breathing_effect(self, screen, center, outer_radius: int, inner_radius: int, elapsed_time: float):
        """Draws a breathing light effect with a deeper color gradient towards the inner circle."""

        pulse_period = 4  # seconds for one full pulse cycle
        pulse_amplitude = outer_radius - inner_radius  # Maximum expansion relative to inner circle
        if elapsed_time > pulse_period:
            return

        # Calculate the pulse offset to animate the gradient effect
        pulse_offset = math.sin(elapsed_time / pulse_period * math.pi / 2)  # Oscillates between 0 and 1
        current_radius = inner_radius + pulse_amplitude * (1 - pulse_offset)  # Decreases from max to min

        # Create a surface for the gradient effect with transparency
        gradient_surface = pygame.Surface((2 * current_radius, 2 * current_radius), pygame.SRCALPHA)

        # Use a higher resolution surface for anti-aliasing effect
        scale_factor = 4  # Increase the resolution by this factor
        high_res_radius = int(current_radius * scale_factor)
        high_res_surface = pygame.Surface((2 * high_res_radius, 2 * high_res_radius), pygame.SRCALPHA)

        # Draw concentric circles with varying intensity to create a gradient effect
        for i in range(high_res_radius, int(inner_radius * scale_factor), -2 * scale_factor):
            color_intensity = int(255 * ((i - inner_radius * scale_factor) / (pulse_amplitude * scale_factor)))
            gradient_color = (255, color_intensity, color_intensity, 128)  # Red gradient with varying alpha

            pygame.draw.circle(high_res_surface, gradient_color, (high_res_radius, high_res_radius), i)

        # Scale down the high-resolution surface to the original size to achieve anti-aliasing
        gradient_surface = pygame.transform.smoothscale(high_res_surface,
                                                        (2 * int(current_radius), 2 * int(current_radius)))

        # Draw the gradient surface on the screen
        screen.blit(gradient_surface, (center[0] - current_radius, center[1] - current_radius))

        # # Draw the inner white circle separately to ensure it stays the correct size
        pygame.draw.circle(screen, (255, 255, 255), center, inner_radius)

    def draw_arrows(self, screen, center: Tuple[int, int], direction: str):
        """Draws left or right arrows based on the direction."""
        if direction == 'left':
            screen.blit(self.left_arrow_image, (
                center[0] - self.left_arrow_image.get_width() // 2,
                center[1] - self.left_arrow_image.get_height() // 2))
        elif direction == 'right':
            screen.blit(self.right_arrow_image, (center[0] - self.left_arrow_image.get_width() // 2,
                                                 center[1] - self.right_arrow_image.get_height() // 2))

    def draw_guidance_text(self, screen):
        """Draws the guidance text for the user."""
        instruction_text = [
            "Please keep looking at the blue dot at all times.",
            "Press \"Space\" to start."
        ]

        self.draw_text_center(screen, instruction_text)

    def draw_text_center(self, screen, text):
        text_surfaces = [self.guidance_font.render(line, True, self._color_black) for line in text]

        total_text_height = sum(text_surface.get_height() for text_surface in text_surfaces) + (
                len(text) - 1) * 10
        start_y = (self.screen_height - total_text_height) // 2

        for i, text_surface in enumerate(text_surfaces):
            text_rect = text_surface.get_rect(
                center=(self.screen_width // 2, start_y + i * (text_surface.get_height() + 10)))
            screen.blit(text_surface, text_rect)

    def _new_session(self):
        self.running = True
        # self.current_point_index = 0  # Start at the first calibration point
        self.start_time = None  # Initialize the start time
        self.sound_played = False  # Flag to track if the sound has been played
        self.point_showing = False
        self.point_elapsed_time = 0

    def check_keys(self, space_continue=True):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
                pygame.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if space_continue:
                    self.running = False

    def draw_previewer(self, screen):
        self._new_session()
        self.et_library.start_previewing()

        while self.running:
            self.check_keys()
            screen.fill(self._color_white)
            image = self.et_library.get_previewer_image()
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            image = cv2.flip(image, 0)
            pygame.surfarray.blit_array(self.previewer_surface, image)
            screen.blit(self.previewer_surface, self.previewer_center)
            pygame.display.flip()

        self.et_library.stop_previewing()

    def draw_calibration(self, screen):
        self.running = True
        while self.running:
            self.check_keys()
            screen.fill(self._color_white)
            self.draw_guidance_text(screen)
            pygame.display.flip()

        self.et_library.start_calibration()
        self.running = True
        while self.running:
            self.check_keys(space_continue=False)
            screen.fill(self._color_white)
            calibration_point: CalibrationPoint = self.et_library.get_calibration_point_info()
            if calibration_point != self._last_drawing_point:
                self.feedback_sound.play()
                self._last_drawing_point = calibration_point

            self.draw_points(screen, calibration_point.x, calibration_point.y, calibration_point.progress)
            pygame.display.flip()

            if self.et_library.is_calibration_finished():
                # self.et_library.get_calibration_result()
                self.running = False
        # print("calibration information:", self.et_library.export_calibration())

    def draw_sampling(self, screen):
        cali_result: CalibrationResult = self.et_library.get_calibration_result()
        render_text_list = []
        if cali_result.status == 1:
            render_text_list.append("校准成功，")
            self.et_library.start_sampling()
        else:
            render_text_list.append("校准失败，模型拟合失败")

        if cali_result.fitting_error != -1:
            render_text_list.append(f"模型误差为 {cali_result.fitting_error} ")

        print(render_text_list)
        self.running = True
        while self.running:
            self.check_keys(space_continue=True)
            screen.fill(self._color_white)
            self.draw_text_center(screen, render_text_list)
            if cali_result.status == 1:
                gaze_info: GazeInfo = self.et_library.get_gaze_info()
                # print(gaze_info)
                self.draw_gaze_cursor(screen, gaze_info)

            pygame.display.flip()
        if cali_result.status == 1:
            self.et_library.stop_sampling()

    # def draw_validation(self, screen):
    # self.draw(screen, "validation")

    def draw_gaze_cursor(self, screen, gaze_info: GazeInfo):
        pygame.draw.circle(screen, self._color_blue, (gaze_info.gaze_x, gaze_info.gaze_y), radius=50, width=3)

    def draw_points(self, screen, x, y, progress):
        # draw green circle
        pygame.draw.circle(screen, self._color_blue, (x, y), 30)

        # draw progress text
        percentage_text = f"{int(progress)}"  # 转换为百分比
        text = self.guidance_font.render(percentage_text, True, self._color_white)  # 白色文字
        text_rect = text.get_rect(center=(x, y))  # 将文字居中
        screen.blit(text, text_rect)

    def draw_calibration_result(self, screen, fitness, is_saved):
        render_text = [
            f"Calibration model fitness is {fitness:.4f} pixel",
            f"Calibration model has been saved" if is_saved else "Calibration model has not been saved",
            f"Press \"Enter\" to validation or \"R\" to recalibration"
        ]
        # print(render_text)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    return False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return True
            screen.fill(self._color_white)
            self.draw_text_center(screen, render_text)
            pygame.display.flip()

    def validation_sample_subscriber(self, face_info, gaze_info, *args, **kwargs):
        """

        :param face_info:
        :param gaze_info:
        :param args:
        :param kwargs:
        :return:
        """
        self.face_info = face_info
        self.gaze_info = gaze_info

    def calculate_d3_metric(self, window=8, stride=1):
        """

        :param window:
        :param stride:
        :return:
        """
        pass

    def draw_error_bar(self, screen, current_point, gaze_coordinates):
        # Draws a green error bar (line) between the current point and gaze coordinates
        # print(gaze_coordinates)
        pygame.draw.line(
            screen,
            self.error_bar_color,
            current_point,
            gaze_coordinates,
            self.error_bar_thickness
        )
        pygame.draw.circle(screen, self._color_red, gaze_coordinates, radius=50, width=3)


# Example usage:
if __name__ == "__main__":
    pass
