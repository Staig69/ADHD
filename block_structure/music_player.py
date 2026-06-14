import pygame
import os


def play_background_music():
    pygame.mixer.init()
    path = os.path.join(os.path.dirname(__file__), "focus_music.mp3")

    if os.path.exists(path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)
    else:
        print("Файл музыки не найден")


def stop_music():
    pygame.mixer.music.stop()