import pygame
import time


class Loading(pygame.sprite.Sprite):
    def __init__(self, image_path, size):
        super().__init__()
        self.original_image = pygame.transform.scale(pygame.image.load(image_path), size)
        self.image = self.original_image.copy()  # Make a copy to avoid modifying the original
        self.rect = self.image.get_rect()
        self.rect.x = 350
        self.rect.y = 341
        self.fill_width = 0

    def update_fill(self, fill_width):
        self.fill_width = fill_width
        self.image = self.original_image.copy()  # Restore the original image
        # Create a mask with curved edges matching the loading progress
        mask_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (97, 161, 208, 255), (0, 0, self.fill_width, self.rect.height), border_radius=10)
        # Apply the mask to the original image
        self.image.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)


def loading(path=""):
    pygame.display.init()
    pygame.font.init()
    image_file_name = path+'neumorphic-rounded-rectangle-free-png.webp'
    sizing = 400, 50

    loading_bar_instance = Loading(image_file_name, sizing)

    # loading text
    surface_width, surface_height = 1100, 650

    font = pygame.font.Font(path+'GROBOLD.ttf', 30)
    loading_text = font.render('Loading...', True, 'white')
    loading_text_rect = loading_text.get_rect()
    loading_text_rect.center = (surface_width // 2, surface_height // 2)

    pygame.image.load(path+'logo.png')

    Bar = pygame.sprite.Group()
    Bar.add(loading_bar_instance)

    display = 1100, 650

    # display chosen
    surface = pygame.display.set_mode(display)

    run = True
    fill_rate = 40  # speed off loading
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        loading_bar_instance.update_fill(loading_bar_instance.fill_width + fill_rate)

        # gradient background
        for y in range(display[1]):
            color = (
                int(29 + 60 * (y / display[1])),  # Red component
                int(30 + 122 * (y / display[1])),  # Green component
                int(34 + 163 * (y / display[1]))  # Blue component
            )
            pygame.draw.line(surface, color, (0, y), (display[0], y))

        surface.blit(loading_text, loading_text_rect)

        Bar.draw(surface)
        pygame.display.update()

        time.sleep(0.1)

        if loading_bar_instance.fill_width >= sizing[0]:
            run = False

    return "success"
