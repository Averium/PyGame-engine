import pygame

from source import Framework


def main():
    pygame.init()
    framework = Framework()
    framework.start()
    pygame.quit()


if __name__ == "__main__":
    main()
