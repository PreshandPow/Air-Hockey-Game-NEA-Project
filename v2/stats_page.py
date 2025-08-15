import pygame
import sqlite3


class Stats():
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

    def player_info(self):
        # Define button properties
        button_width = 400
        button_height = 550
        button_x = 50
        button_y = 50
        button_color = (255, 255, 255)
        text_color = (0, 0, 0)

        trophies = self.data_store.get_data('trophies')
        pvp_wins = self.data_store.get_data('pvp_wins')
        pvp_losses = self.data_store.get_data('pvp_losses')
        pve_wins = self.data_store.get_data('pve_wins')
        pve_losses = self.data_store.get_data('pve_losses')
        arena = self.data_store.get_data('arena')
        arena_name = None

        if arena == 1:
            arena_name = 'Neon City'

        if arena == 2:
            arena_name = 'Underwater Kingdom'


        # Create a Pygame font
        font = pygame.font.Font('../LEMONMILK-Bold.otf', 18)

        # Define button rectangle
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Draw the button
        pygame.draw.rect(self.surface, button_color, button_rect)

        "trophies text"
        trophies_text_surface = font.render('Total Trophies', True, text_color)
        trophies_surface = font.render(f'{trophies}', True, text_color)

        self.surface.blit(trophies_text_surface, (65, 50))
        self.surface.blit(trophies_surface, (65, 75))

        "pvp wins text"
        pvp_wins_text_surface = font.render('Player Vs Player (PVP) Wins', True, text_color)
        pvp_wins_surface = font.render(f'{pvp_wins}', True, text_color)

        self.surface.blit(pvp_wins_text_surface, (65, 110))
        self.surface.blit(pvp_wins_surface, (65, 140))

        "pvp_losses text"
        pvp_losses_text_surface = font.render('Player Vs Player (PVP) Losses', True, text_color)
        pvp_losses_surface = font.render(f'{pvp_losses}', True, text_color)

        self.surface.blit(pvp_losses_text_surface, (65, 190))
        self.surface.blit(pvp_losses_surface, (65, 220))

        "pve_wins text"
        pve_wins_text_surface = font.render('Player Vs Environment (PVE) Wins', True, text_color)
        pve_wins_surface = font.render(f'{pve_wins}', True, text_color)

        self.surface.blit(pve_wins_text_surface, (60, 270))
        self.surface.blit(pve_wins_surface, (60, 300))

        "pve_losses_text"
        pve_losses_text_surface = font.render('Player Vs Environment (PVE) Wins', True, text_color)
        pve_losses_surface = font.render(f'{pve_losses}', True, text_color)

        self.surface.blit(pve_losses_text_surface, (60, 350))
        self.surface.blit(pve_losses_surface, (60, 380))

        "arena_test"
        arena_text_surface = font.render('Arena ', True, text_color)
        arena_surface = font.render(f'{arena_name}({arena})', True, text_color)

        self.surface.blit(arena_text_surface, (65, 430))
        self.surface.blit(arena_surface, (65, 460))




    def show_screen(self):
        pygame.display.set_caption('Statistics Page!!!')
        run = True
        while run:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    run = False

            self.surface.fill(self.OUTER_SPACE)
            re = self.draw_return_button()
            self.player_info()
            if re == 'menu':
                return 'back'
            pygame.display.update()


surface_width, surface_height = 1100, 650
surface = pygame.display.set_mode((surface_width, surface_height))
paddle = None
session_info = None

