import pygame
from pygame.locals import *
from PIL import Image

class UnderwaterArena:
    def __init__(self, width=1100, height=650):
        pygame.init()

        # Set up display
        self.width = width
        self.height = height
        self.window = pygame.Surface((self.width, self.height))
        pygame.display.set_caption("Underwater Arena")

        # Load resources (replace paths with actual image files)
        self.floor_frames = self.load_and_transform_gif('../underwater_floor.gif', 0, (self.width, self.height))
        self.steering_wheel_frames = self.load_and_transform_gif('../pirate_ship_wheel.gif', 0, (150, 150))

        # Border properties
        self.light_blue = (173, 216, 230)  # Default border color
        self.neon_blue = (0, 0, 128)  # Pulsating color when hit
        self.border_color = self.light_blue
        self.border_thickness = 12
        self.border_pulse_timer = 0

        # Frame index to track animation
        self.floor_index = 0
        self.wheel_index = 0

    def load_and_transform_gif(self, gif_path, rotation_angle, new_size):
        gif = Image.open(gif_path)
        frames = []
        try:
            while True:
                frame = gif.convert('RGBA')
                mode = frame.mode
                size = frame.size
                data = frame.tobytes()
                pygame_image = pygame.image.fromstring(data, size, mode)

                # Rotate and resize
                rotated_frame = pygame.transform.rotate(pygame_image, rotation_angle)
                resized_frame = pygame.transform.scale(rotated_frame, new_size)

                frames.append(resized_frame)
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        return frames

    def update(self):
        # Update animation indices
        self.floor_index = (self.floor_index + 1) % len(self.floor_frames)
        self.wheel_index = (self.wheel_index + 1) % len(self.steering_wheel_frames)

        # Handle border pulsation
        if self.border_pulse_timer > 0:
            self.border_pulse_timer -= 1
            if self.border_pulse_timer == 0:
                self.border_color = self.light_blue  # Reset to default color

    def draw(self, surface):
        # Draw animated underwater floor
        surface.blit(self.floor_frames[self.floor_index], (0, 0))

        # Draw animated steering wheel at the centre
        surface.blit(self.steering_wheel_frames[self.wheel_index], (self.width // 2 - 75, self.height // 2 - 75))

        # Draw pulsating borders (excluding goal gaps)
        pygame.draw.rect(surface, self.border_color, (0, 0, self.width, self.border_thickness))  # Top
        pygame.draw.rect(surface, self.border_color, (0, self.height - self.border_thickness, self.width, self.border_thickness))  # Bottom
        pygame.draw.rect(surface, self.border_color, (0, 0, self.border_thickness, 250))  # Left upper
        pygame.draw.rect(surface, self.border_color, (0, 450, self.border_thickness, 200))  # Left lower
        pygame.draw.rect(surface, self.border_color, (self.width - self.border_thickness, 0, self.border_thickness, 250))  # Right upper
        pygame.draw.rect(surface, self.border_color, (self.width - self.border_thickness, 450, self.border_thickness, 200))  # Right lower

    def border_hit(self):
        self.border_color = self.neon_blue  # Change to neon blue
        self.border_pulse_timer = 30  # Stay neon for 30 frames

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

            self.update()
            self.draw(self.window)

            pygame.display.flip()
            clock.tick(120)

# Usage example
# board = UnderwaterArena(1100, 650)
# while True:
#     board.update()
#     board.draw(surface)  # Main game surface
#     pygame.display.flip()
