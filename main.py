# _*_ coding: utf-8 _*_
# Author: GC Zhu
# Email: zhugc2016@gmail.com
import ctypes

import pygame
from pygame import FULLSCREEN, HWSURFACE

from core import TCCIDesktopET
from graphics import Graphics

# initialize TCCIDesktopET
et_library = TCCIDesktopET()
et_library.eye_tracking_init(cam_id=0, look_ahead=2, preprocessing_type=1)

print("Starting eye tracking registration process...")
expired_days = et_library.eye_tracking_register("c8f076bc10dd43d6")
if expired_days > 0:
    print(f"Registration successful! License valid for {expired_days} days.")
else:
    print("Registration failed. The license has expired.")
    exit(0)

# initialize PyGame
pygame.init()
# scree size
screen_size = (1920, 1080)
# open a window in fullscreen mode
screen = pygame.display.set_mode(screen_size, FULLSCREEN | HWSURFACE)

g = Graphics(et_library=et_library)
g.draw_previewer(screen=screen)
g.draw_calibration(screen=screen)
g.draw_sampling(screen=screen)