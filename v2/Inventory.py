import pygame
import sqlite3


class Inventory():
    def __init__(self, surface, paddle, session_info):
        pygame.init()
        self.surface = surface
        self.paddle = paddle
        self.data_store = session_info
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.MINT_GREEN = (194, 239, 235)
        self.CERULEAN = (0, 126, 167)
        self.POMP_AND_POWER = (161, 103, 165)
        self.TEKHELET = (74, 48, 109)
        self.MOONSTONE = (0, 159, 183)
        self.PALINSTINATE_BLUE = (35, 46, 209)
        self.RICH_BLACK = (14, 19, 23)
        self.OUTER_SPACE = (67, 80, 88)

    def draw_return_button(self):
        # Define button properties
        button_width = 200
        button_height = 50
        button_x = 875
        button_y = 575
        button_color = (255, 0, 0)  # Red color
        text_color = (255, 255, 255)  # White color

        # Create a Pygame font
        font = pygame.font.Font('../LEMONMILK-Bold.otf', 18)

        # Define button rectangle
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Draw the button
        pygame.draw.rect(self.surface, button_color, button_rect)

        # Render the text
        text_surface = font.render('Return to Menu', True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)

        # Blit the text onto the button
        self.surface.blit(text_surface, text_rect)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        print("Return button pressed!")
                        return 'menu'

    def show_screen(self):
        pygame.display.set_caption('Inventory')
        run = True
        while run:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    run = False

            self.surface.fill(self.OUTER_SPACE)
            re = self.draw_return_button()
            if re == 'menu':
                return 'back'
            pygame.display.update()


surface_width, surface_height = 1100, 650
surface = pygame.display.set_mode((surface_width, surface_height))
paddle = None
session_info = None

