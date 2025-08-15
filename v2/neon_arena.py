import pygame
from pygame.locals import *
from PIL import Image

class neonBoard:
    def __init__(self, width=1100, height=650):
        # Initialize Pygame
        pygame.init()

        # Initialize colors
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

        self.colours = ['red', 'blue', 'white', 'purple', 'green']

        # Set up display
        self.width = width
        self.height = height
        self.window = pygame.Surface((self.width, self.height))
        pygame.display.set_caption("Neon Arena")

        # Load resources
        self.gif1_frames = self.load_and_transform_gif('../neon goals.gif', 90, (200, 200))
        self.gif2_frames = self.load_and_transform_gif('../neon goals.gif', 90, (200, 200))
        self.background = pygame.transform.scale(pygame.image.load('../background 2.jpg'), (self.width, self.height))

        # Frame index to track current frame
        self.frame_index = 0

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

                # Rotate and resize the frame
                rotated_frame = pygame.transform.rotate(pygame_image, rotation_angle)
                resized_frame = pygame.transform.scale(rotated_frame, new_size)

                frames.append(resized_frame)
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass  # End of sequence

        return frames

    def update(self):
        # Update the frame index to loop through GIF frames
        self.frame_index = (self.frame_index + 1) % len(self.gif1_frames)

    def draw(self, surface):
        # Fill the surface with the background color
        surface.fill(self.RICH_BLACK)

        # Draw the GIF frames
        surface.blit(self.gif1_frames[self.frame_index], (-86, 225))  # Adjust position as needed
        surface.blit(self.gif2_frames[self.frame_index], (996, 225))  # Adjust position as needed

        # Draw central line and circle
        pygame.draw.line(surface, self.MOONSTONE, (self.width // 2, 0), (self.width // 2, self.height), 5)
        pygame.draw.circle(surface, self.MOONSTONE, (self.width // 2, self.height // 2), 70)
        pygame.draw.circle(surface, self.RICH_BLACK, (self.width // 2, self.height // 2), 64)

        # Draw borders
        pygame.draw.line(surface, self.OUTER_SPACE, (0, 0), (0, 243), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (0, 405), (0, 650), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (1098, 0), (1098, 243), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (1098, 405), (1098, 650), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (0, 0), (275, 0), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (275, 0), (547, 0), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (553, 0), (825, 0), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (825, 0), (1100, 0), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (0, 648), (275, 648), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (275, 648), (547, 648), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (553, 648), (825, 648), 12)
        pygame.draw.line(surface, self.OUTER_SPACE, (825, 648), (1100, 648), 12)

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


# Usage in the game loop
# board = neonBoard(1100, 650)
# while True:
#     board.update()
#     board.draw(surface)  # Surface is the main game window where everything is drawn
#     # Draw other game elements here...
#     pygame.display.flip()
