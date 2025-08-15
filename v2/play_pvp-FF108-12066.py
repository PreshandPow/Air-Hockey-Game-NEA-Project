import socket
import json
import pygame
import sys
import sqlite3
from neon_arena import neonBoard
import threading

# Initialize Pygame
pygame.display.init()
pygame.font.init()

# Set up the display
surface_width, surface_height = 1100, 650
surface = pygame.display.set_mode((surface_width, surface_height))
pygame.display.set_caption('Air Hockey!')

# Define Colors
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
MINT_GREEN = (194, 239, 235)
CERULEAN = (0, 126, 167)
POMP_AND_POWER = (161, 103, 165)
TEKHELET = (74, 48, 109)
MOONSTONE = (0, 159, 183)
PALINSTINATE_BLUE = (35, 46, 209)
RICH_BLACK = (14, 19, 23)
OUTER_SPACE = (67, 80, 88)

# Configuration for client connection
HEADER = 1024
PORT = 5055
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT!'
SERVER = '192.168.0.26'
ADDR = (SERVER, PORT)


# class to calculate math and physic equations to manipulate x and y positions of the paddle and puck
class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    # adding vectors
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    # subtracting vectors
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    # multiplying vectors
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    # dividing vectors
    def __truediv__(self, scalar):
        return Vector(self.x / scalar)

    # pythagorean theorem
    def length(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    #
    def normalise(self):
        length = self.length()
        if length != 0:
            return Vector(self.x / length, self.y / length)
        return Vector()

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def limit(self, max_length):
        length = self.length()
        if length > max_length:
            return self.normalise() * max_length
        return self


# the class for the paddle's taking in 6 attributes
class Paddle(pygame.sprite.Sprite):
    def __init__(self, start_pos, color, radius, side, client, speed=6, power=1):  # Increased power
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # paddle outline
        pygame.draw.circle(self.image, BLACK, (radius, radius), 21)  # black centre of the paddle
        if not isinstance(start_pos, tuple) or len(start_pos) != 2:
            raise ValueError(f"Start position is not correctly defined: {start_pos}")

        self.rect = self.image.get_rect(center=start_pos)
        self.rect_x = self.rect.x
        self.rect_y = self.rect.y
        self.color = color  # colour of paddle
        self.radius = radius  # radius/size of paddle
        self.holding = False  # if the paddle is being held/clicked on
        self.side = side  # the edges of the paddle
        self.velocity = Vector()  # call the vector function
        self.start_pos = start_pos  # the start position of the paddle at the beginning of every round
        self.speed = speed  # the speed of the paddle
        self.power = power  # the power at which the paddle hits the puck
        self.puck = None
        self.client = client

    def set_puck(self, puck):
        self.puck = puck

    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def update_opponent_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def send_message(self, msg):
        if self.client:
            try:
                message = msg.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Failed to send message: {e}')

    def send_position_data(self):
        if self.client:  # Check if client socket is initialized
            try:
                position_data = json.dumps({'x': self.rect.x, 'y': self.rect.y})
                message = position_data.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Error sending position data: {e}')
                self.client.close()  # Close the socket upon an error
                self.client = None  # Nullify the client socket reference

    # update events in correspondence with the paddle's
    def update(self, events):
        if self.side == 'left':  # player paddle
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.rect.collidepoint(event.pos):
                        self.holding = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.holding = False
                # find out whether the player_paddle is being held or not

            # if the paddle is being held the player can move the paddle dependent on their mouse position
            if self.holding:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                new_velocity = Vector(mouse_x - self.rect.centerx, mouse_y - self.rect.centery)
                self.velocity = new_velocity.limit(self.speed)
                self.rect.center = (mouse_x, mouse_y)
            else:
                self.velocity = Vector()

        elif self.side == 'right':  # player paddle
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.rect.collidepoint(event.pos):
                        self.holding = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.holding = False
                # find out whether the player_paddle is being held or not

            # if the paddle is being held the player can move the paddle dependent on their mouse position
            if self.holding:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                new_velocity = Vector(mouse_x - self.rect.centerx, mouse_y - self.rect.centery)
                self.velocity = new_velocity.limit(self.speed)
                self.rect.center = (mouse_x, mouse_y)
            else:
                self.velocity = Vector()

        # restrict paddle movement, so it can't come off the board
        if self.side == 'left':
            if self.rect.right > surface_width // 2:
                self.rect.right = surface_width // 2
            if self.rect.left < 0:
                self.rect.left = 0

        if self.side == 'right':
            if self.rect.left < surface_width // 2:
                self.rect.left = surface_width // 2
            if self.rect.right > surface_width:
                self.rect.right = surface_width

        # keep the paddle within vertical bounds
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > surface_height:
            self.rect.bottom = surface_height

    # function to reset the paddle's position
    def reset_position(self):
        self.rect.center = self.start_pos

    # draw the paddle's unto the board
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


# the class for the puck taking in 3 attributes
class Puck(pygame.sprite.Sprite):
    def __init__(self, start_pos, color, radius, client):
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # the puck
        self.rect = self.image.get_rect(center=start_pos)  # the puck's rect
        self.rect_x = self.rect.x
        self.rect_y = self.rect.y
        self.color = color  # the colour of the puck
        self.radius = radius  # the radius/size of the puck
        self.velocity = Vector(0, 0)  # initial velocity slightly increased
        self.friction = 0.99  # the friction so the puck slows down over time
        self.max_speed = 20  # the maximum speed which the puck can move at
        self.min_speed = 0.00000000001  # the minimum speed the puck can move at
        self.start_pos = start_pos  # the starting position of the puck
        self.position = start_pos
        self.client = client

    # the method to update all game events in correspondence with the puck
    def update(self):
        # apply friction
        self.velocity *= self.friction

        # limit its maximum speed
        self.velocity = self.velocity.limit(self.max_speed)

        # if its velocity is very low, stop the puck
        if self.velocity.length() < self.min_speed:
            self.velocity = Vector()

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # bounce off top and bottom edges
        if self.rect.top <= 0 or self.rect.bottom >= surface_height:
            self.velocity.y *= -1
            # Correct puck position
            if self.rect.top <= 0:
                self.rect.top = 0
            elif self.rect.bottom >= surface_height:
                self.rect.bottom = surface_height

        # bounce off left and right edges
        if self.rect.left <= 0 or self.rect.right >= surface_width:
            self.velocity.x *= -1
            # correct the puck's position
            if self.rect.left <= 0:
                self.rect.left = 0
            elif self.rect.right >= surface_width:
                self.rect.right = surface_width

    def update_puck_position(self, x, y):
        if self.rect.x != x or self.rect.y != y:
            self.rect.x = x
            self.rect.y = y
            print(f'puck position update: x={x} and y={y}')

    def send_message(self, msg):
        if self.client:
            try:
                message = msg.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Failed to send message: {e}')

    def position_data(self, pp, user, id):
        if self.client:
            try:
                position_data = json.dumps({'id': id, 'puck_x': self.rect.x, 'puck_y': self.rect.y})
                message = position_data.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Failed to send puck position data: {e}')
                self.client.close()
                self.client = None

    # reset the puck's position/its x and y values and its velocity
    def reset_position(self):
        self.rect.center = self.start_pos
        self.velocity = Vector(0, 0)  # Reset velocity

    # draw the puck on the board
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


# the class for the hockey board it takes in 2 attributes

class Pvp:
    def __init__(self, surface, player_pos, opponent_pos, client, username, player_id, trophies):
        self.surface = surface
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
        self.player_position = player_pos
        self.opponent_pos = opponent_pos
        self.client = client
        self.opp_pos = 950, 350
        self.puck_pos = 550, 325
        self.player_username = username
        self.player_id = player_id
        self.trophies = trophies

        self.opponent_paddle = Paddle(self.opp_pos, self.RED, 37, 'right', speed=4, power=0.00000000001,
                                      client=self.client)

        self.puck = Puck(self.puck_pos, self.WHITE, 30, client=self.client)

        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()

    def runsql(self, *args):
        conn = sqlite3.connect('../air_hockey.db')
        conn.execute('PRAGMA foreign_keys = 1')
        cursor = conn.cursor()
        if len(args) == 1:
            cursor.execute(args[0])
        else:
            cursor.execute(args[0], args[1])
        conn.commit()
        return cursor.fetchall()

    # function to check whether a goal has been scored

    def player_goal(self):
        if self.player_position == 1:
            if self.puck.rect.x >= 1100: and 250 <= self.puck.recy.y <= 400:


    # draw text unto the board(player_score and opponent_score)
    def draw_text(self, surface, text, font, color, pos):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, pos)

    def handle_collisions(self, puck, paddle):
        if puck.rect.colliderect(paddle.rect):
            normal = Vector(puck.rect.centerx - paddle.rect.centerx,
                            puck.rect.centery - paddle.rect.centery).normalise()
            relative_velocity = puck.velocity - paddle.velocity
            velocity_along_normal = relative_velocity.dot(normal)

            # reflect the puck's velocity along the normal
            if velocity_along_normal < 0:  # Ensure we only reflect if moving towards the paddle
                puck.velocity = puck.velocity - normal * (2 * velocity_along_normal)

            # increase puck velocity based on paddle power
            puck.velocity += normal * paddle.power  # Adjust puck velocity by paddle power

            # move puck out of collision
            while puck.rect.colliderect(paddle.rect):
                puck.rect.x += normal.x
                puck.rect.y += normal.y

    # the function to show the winner of the game

    def display_winner(self, surface, text):
        font = pygame.font.Font('../LEMONMILK-Medium.otf', 62)
        text_surf = font.render(text, True, BLACK)
        surface.blit(text_surf, (200, 150))
        pygame.display.flip()
        pygame.time.delay(2000)

    def listen_for_server_messages(self):
        while True:
            try:
                # Receive and decode the message
                msg = self.client.recv(1024).decode(FORMAT)
                position_data = json.loads(msg)

                if 'x' in position_data and 'y' in position_data:  # Opponent paddle data
                    new_position = (position_data['x'], position_data['y'])
                    self.opponent_paddle.update_opponent_position(*new_position)
                    # print(f'Opponent paddle position updated: {new_position}')  # Debugging log

                elif 'puck_x' in position_data and 'puck_y' in position_data:  # Puck data
                    new_puck_position = (position_data['puck_x'], position_data['puck_y'])
                    self.puck.update_puck_position(*new_puck_position)
                    # print(f"Puck position updated to: x={self.puck.rect.x}, y={self.puck.rect.y}")
                    # print(f'Puck position updated: {new_puck_position}')  # Debugging log


                else:
                    print(f"Invalid position data received: {position_data}")

            except json.JSONDecodeError:
                print("Error decoding JSON message.")
            except Exception as e:
                print(f"Error receiving server message: {e}")

    def win(self):
        if self.client:
            try:
                self.client.send('win'.encode(FORMAT))
                font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
                font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
                win = font1.render(f'You have won!!!', True, BLACK)
                result = font2.render('You have gained 5 trophies', True, BLACK)
                surface.blit(win, (450, 300))
                surface.blit(result, (435, 350))
                pygame.display.flip()
                pygame.time.delay(1000)

            except Exception as e:
                print(f'Error sending win to server: {e}')

    def loss(self):
        if self.client:
            try:
                self.client.send('loss'.encode(FORMAT))
                font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
                font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
                win = font1.render(f'You have lost!!!', True, BLACK)
                result = font2.render('You have lost 5 trophies', True, BLACK)
                surface.blit(win, (450, 300))
                surface.blit(result, (435, 350))
                pygame.display.flip()
                pygame.time.delay(1000)

            except Exception as e:
                print(f'Error sending win to server: {e}')

    def show_screen(self):
        # Initial Scores
        player_score = 0
        opponent_score = 0
        max_score = 3

        font = pygame.font.Font('../LEMONMILK-Medium.otf', 32)

        # Initialize objects
        # Proper start positions
        player1_start_position = (150, 325)
        opponent_start_position = (950, 325)

        # Conditional initialization based on player position
        if self.player_position == 1:
            print('I AM PLAYER 1')
            player_paddle = Paddle(player1_start_position, self.BLUE, 37, 'left', speed=4, power=0.00000000001,
                                   client=self.client)
            self.opponent_paddle = Paddle(opponent_start_position, self.RED, 37, 'right', speed=4, power=0.00000000001,
                                          client=self.client)
        else:
            print('I AM PLAYER 2')
            player_paddle = Paddle(opponent_start_position, self.RED, 37, 'right', speed=4, power=0.00000000001,
                                   client=self.client)
            self.opponent_paddle = Paddle(player1_start_position, self.BLUE, 37, 'left', speed=4, power=0.00000000001,
                                          client=self.client)

        puck_start_position = (surface_width // 2, surface_height // 2)
        # puck = Puck(puck_start_position, self.WHITE, 30, client=self.client)

        board = neonBoard(1100, 650)
        # player_paddle.set_puck(self.puck)

        print(self.player_username)

        clock = pygame.time.Clock()

        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()

        while opponent_score != max_score and player_score != max_score:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Update game objects
            player_paddle.update(events)
            self.puck.update()

            pp = None
            if self.player_position == 1:
                pp = 1
            elif self.player_position == 2:
                pp = 2

            player_paddle.send_position_data()
            self.puck.position_data(pp, self.player_username, self.player_id)
            # print(f"Puck rendering at: x={self.puck.rect.x}, y={self.puck.rect.y}")

            # Handle collisions
            self.handle_collisions(self.puck, player_paddle)

            # Check for goals
            player_score = self.check_goal(self.puck, player_score, player_paddle)
            print(player_score)

            # Update and draw the board
            board.update()
            board.draw(self.surface)

            # Draw the game objects
            player_paddle.draw(self.surface)
            self.opponent_paddle.draw(self.surface)  # Draw opponent paddle
            # print(f'puck pos before being drawn: x={self.puck.rect.x}, y={self.puck.rect.y}') # Debug
            self.puck.draw(self.surface)
            # print(f'puck pos after being drawn: x={self.puck.rect.x}, y={self.puck.rect.y}') # Debug

            if self.player_position == 1:
                display_player_name = font.render(self.player_username, True, BLUE)
                display_opponent_name = font.render('Opponent', True, RED)
                surface.blit(display_player_name, (125, 10))
                surface.blit(display_opponent_name, (850, 10))

            else:
                display_player_name = font.render(self.player_username, True, RED)
                display_opponent_name = font.render('Opponent', True, BLUE)
                surface.blit(display_player_name, (850, 10))
                surface.blit(display_opponent_name, (75, 10))

            display_player_score = font.render(f'{player_score}', True, BLACK)
            display_opponent_score = font.render(f'{opponent_score}', True, BLACK)

            surface.blit(display_player_score, (495, 10))
            surface.blit(display_opponent_score, (580, 10))

            pygame.display.flip()
            clock.tick(120)

        if player_score >= max_score:
            self.display_winner(self.surface, f"Player 1 Wins: {None} trophies gained!")
            self.win()
        elif opponent_score >= max_score:
            self.display_winner(self.surface, f"You have lost: {None} trophies lost!")
            self.loss()