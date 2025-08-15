import pygame
from PIL import Image, ImageSequence
import sqlite3


class Menu:
    def __init__(self, surface, session_info, gif_path):
        self.surface = surface
        self.data_store = session_info
        self.gif_path = gif_path
        self.gif_frames = self.load_gif()
        self.current_frame = 0
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

    def load_gif(self):
        gif = Image.open(self.gif_path)
        frames = []
        surface_width, surface_height = self.surface.get_size()

        try:
            while True:
                frame = gif.copy().convert('RGBA')
                frame = frame.resize((surface_width, surface_height), Image.LANCZOS)
                frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                frames.append(frame)
                gif.seek(len(frames))
        except EOFError:
            pass

        return frames

    def runsql(self, query, values=None):
        conn = sqlite3.connect('air_hockey.db')
        conn.execute('PRAGMA foreign_keys = 1')
        cursor = conn.cursor()
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()

    def get_trophies(self):
        username = self.data_store.get_data('username')
        id = self.data_store.get_data("id")
        if not id:
            raise ValueError("Player ID not found in data store")
        query = '''
            SELECT totalTrophies
            FROM tblPlayerStats
            WHERE playerId = ?
        '''
        values = (id,)
        trophies_result = self.runsql(query, values)
        result = trophies_result[0][0] if trophies_result else 0
        self.data_store.add_data('trophies', result)
        return result

    def draw_pvp(self, surface, mouse_pos, events):
        button_rect = pygame.Rect(320, 495, 155, 80)

        if button_rect.collidepoint(mouse_pos):
            font = pygame.font.Font("../LEMONMILK-Bold.otf", 28)
            pygame.draw.rect(surface, self.MOONSTONE, (325, 498, 143, 75), border_radius=14)
            pygame.draw.rect(surface, self.CERULEAN, (330, 503, 133, 65), border_radius=12)
            pve_text = font.render("PVP", True, self.BLACK)
            surface.blit(pve_text, (367, 515))

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if button_rect.collidepoint(event.pos):
                            print("PVP button pressed!")
                            print('Matchmaking!')
                            return 'pvp'
        else:
            font = pygame.font.Font("../LEMONMILK-Bold.otf", 28)
            pygame.draw.rect(surface, self.MOONSTONE, (320, 495, 155, 80), border_radius=14)
            pygame.draw.rect(surface, self.CERULEAN, (325, 500, 145, 70), border_radius=12)
            pve_text = font.render("PVP", True, self.BLACK)
            surface.blit(pve_text, (367, 515))

    def draw_pve(self, surface, mouse_pos, events):
        button_rect = pygame.Rect(625, 495, 155, 80)

        if button_rect.collidepoint(mouse_pos):
            font = pygame.font.Font("../LEMONMILK-Bold.otf", 28)
            pygame.draw.rect(surface, self.MOONSTONE, (630, 498, 143, 75), border_radius=14)
            pygame.draw.rect(surface, self.CERULEAN, (635, 503, 133, 65), border_radius=12)
            pve_text = font.render("PVE", True, self.RICH_BLACK)
            surface.blit(pve_text, (672, 515))

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if button_rect.collidepoint(event.pos):
                            print("PVE button pressed!")
                            return 'pve'
        else:
            font = pygame.font.Font("../LEMONMILK-Bold.otf", 28)
            pygame.draw.rect(surface, self.MOONSTONE, (625, 495, 155, 80), border_radius=14)
            pygame.draw.rect(surface, self.CERULEAN, (630, 500, 145, 70), border_radius=12)
            pve_text = font.render("PVE", True, self.RICH_BLACK)
            surface.blit(pve_text, (672, 515))

    def draw_inventory(self, surface, mouse_pos, events):
        button_rect = pygame.Rect(900, 300, 143, 75)

        if button_rect.collidepoint(mouse_pos):
            font = pygame.font.Font('../LEMONMILK-Bold.otf', 18)
            pygame.draw.rect(surface, self.OUTER_SPACE, (905, 302, 143, 75), border_radius=14)
            pve_text = font.render("Inventory", True, self.BLACK)
            surface.blit(pve_text, (917, 325))

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if button_rect.collidepoint(event.pos):
                            print("Inventory opened!")
                            return 'inv'

        else:
            font = pygame.font.Font('../LEMONMILK-Bold.otf', 18)
            pygame.draw.rect(surface, self.TEKHELET, (900, 300, 150, 80), border_radius=14)
            pve_text = font.render("Inventory", True, self.MOONSTONE)
            surface.blit(pve_text, (917, 325))

    def draw_banner(self, surface, mouse_pos, events):
        pygame.draw.rect(surface, self.MOONSTONE, (25, 25, 400, 150), border_radius=25)
        # pygame.draw.rect(surface, self.OUTER_SPACE, (350, 100, 175, 100), border_radius=15)
        trophy = pygame.transform.scale(pygame.image.load(
            "../kisspng-computer-icons-trophy-encapsulated-postscript-winner-5abb2925c72b39.3639625415222152058158.png"),
            (75, 75))
        trophy_rect = trophy.get_rect(topleft=(28, 60))
        surface.blit(trophy, trophy_rect)
        font = pygame.font.Font('../LEMONMILK-Bold.otf', 38)

        if trophy_rect.collidepoint(mouse_pos):
            currency = font.render(f'{self.get_trophies()}', True, self.OUTER_SPACE)
            surface.blit(currency, (125, 75))
        else:
            name = font.render(f'{self.data_store.get_data("username")}', True, self.OUTER_SPACE)
            surface.blit(name, (125, 75))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if trophy_rect.collidepoint(event.pos):
                        print("Stats page opened")
                        return 'stats'

    def draw(self, surface):
        frame = self.gif_frames[self.current_frame]
        surface.blit(frame, (0, 0))
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)

    def show_screen(self):
        surface_width, surface_height = 1100, 650
        surface = pygame.display.set_mode((surface_width, surface_height))

        run = True
        clock = pygame.time.Clock()
        while run:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    run = False

            mouse_pos = pygame.mouse.get_pos()
            self.draw(surface)
            stat_result = self.draw_banner(surface, mouse_pos, events)
            pve_result = self.draw_pve(surface, mouse_pos, events)
            pvp_result = self.draw_pvp(surface, mouse_pos, events)
            inventory_result = self.draw_inventory(surface, mouse_pos, events)

            if pve_result == 'pve':
                return 'pve'

            if pvp_result == 'pvp':
                return 'pvp'

            if inventory_result == 'inv':
                return 'inv'

            if stat_result == 'stats':
                # print('stat')
                return 'stat'



            pygame.display.update()
            clock.tick(10)  # Adjust the frame rate as
