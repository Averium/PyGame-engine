import pygame

from source import Framework


def main():
    pygame.init()
    framework = Framework()
    framework.start()
    pygame.quit()


if __name__ == "__main__":
    main()


# TODO:
#  Update theme handling to a more dynamic approach and add a theme switch or dropdown
#  Sometimes there is a wierd flickering in actuated signals (possibly comes from C side)
#  Something is wrong with the force vector X and Y coordinate length ratio
#  Rework source code of RequestScreen and AllocationScreen widgets (they are too complicated)
