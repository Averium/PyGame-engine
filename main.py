import pygame
from game import Framework


def main():
    pygame.init()
    framework = Framework()
    framework.start()
    pygame.quit()


if __name__ == "__main__":
    main()


# TODO
#  Sprite extension
#  Animation system
