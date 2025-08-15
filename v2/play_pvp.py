import socket
import json
from operator import truediv

import pygame
import sys
import sqlite3
from neon_arena import neonBoard
import threading
import random

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
game_duration = 180  # 3 minutes in seconds
sudden_death_duration = 60  # 1 minute in seconds
time_remaining = game_duration
sudden_death_active = False
clock = pygame.time.Clock()  # Ensure smooth timing updates

# Configuration for client connection
HEADER = 1024
PORT = 5055
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT!'
SERVER = '192.168.0.26'
ADDR = (SERVER, PORT)


# class to calculate math and physic equations to manipulate x and y positions of the paddle and puck
class Vector:

    # initialises a vector within x and yt coordinates
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    # adding vectors
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    # subtracting vectors
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    # multiplying vectors by a scalar
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    # dividing vectors by a scalar
    def __truediv__(self, scalar):
        return Vector(self.x / scalar)

    # pythagorean theorem. Returns magnitude of the vector
    def length(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    # the function converts the vector into a unit vector by dividing the x and y by the length (magnitude)
    def normalise(self):
        length = self.length()
        if length != 0:
            return Vector(self.x / length, self.y / length)
        return Vector()

    # Calculates the dot product of two vectors. The dot product measures how much two vectors point in the same direction
    def dot(self, other):
        return self.x * other.x + self.y * other.y

    # limits the magnitude of the vector to max length
    def limit(self, max_length):
        length = self.length()
        if length > max_length:
            return self.normalise() * max_length
        return self


# the class for the paddle's taking in 6 attributes
class Paddle(pygame.sprite.Sprite):

    # initialises a paddle with position, speed, power and connection data
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

    # associates the paddle with the puck
    def set_puck(self, puck):
        self.puck = puck

    # updates the paddle's position
    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    # updates the opponent paddle's position
    def update_opponent_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    # sends a message to the server
    def send_message(self, msg):
        if self.client:
            try:
                message = msg.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Failed to send message: {e}')

    # sends the paddle's position to the server
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

    # handles paddle movement based on user input
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


# initialises the puck with position, velocity and physics properties
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
        self.friction = 0.98  # the friction so the puck slows down over time
        self.max_speed = 50  # the maximum speed which the puck can move at
        self.min_speed = 0  # the minimum speed the puck can move at
        self.start_pos = start_pos  # the starting position of the puck
        self.position = start_pos
        self.client = client
        self.collision_detected = False
        self.opponent_collision_detected = False

    # updates the puck's position based on velocity and applies friction
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

    # updates the puck's position
    def update_puck_position(self, x, y):
        # if self.rect.x != x or self.rect.y != y:
        self.rect.x = x
        self.rect.y = y
        # print(f'puck position update: x={x} and y={y}')

    # sends a message to the server
    def send_message(self, msg):
        if self.client:
            try:
                message = msg.encode(FORMAT)
                send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                self.client.send(send_length)
                self.client.send(message)
            except Exception as e:
                print(f'Failed to send message: {e}')

    # checks if the puck collides with the player's paddle
    @staticmethod
    def detect_collision(puck, paddle):
        if puck.rect.colliderect(paddle.rect):
            print('collision detected with player paddle')
            return True
        return False

    # checks if the puck collides with the opponent's paddle
    @staticmethod
    def opponent_collision(puck, opponent):
        if puck.rect.colliderect(opponent.rect):
            print('opponent collision detected')
            return True
        return False

    # determines if the puck's position should be sent to the server
    def prepare_to_send(self, pp, x, y):
        # If a collision has been detected, keep sending until opponent collides
        if self.collision_detected:
            print('sending puck position (collision detected)')
            return True

            # If the opponent collides, reset collision flag
        if self.opponent_collision_detected:
            print('opponent collision detected, stopping send')
            self.collision_detected = False
            self.opponent_collision_detected = False  # Reset after handling

        # Normal conditions: Player 1 sends when puck is on left, Player 2 sends when puck is on right
        if (pp == 1 and x <= 550) or (pp == 2 and x > 550):
            return True

        return False

    # handles sending puck position updates to the server
    def position_data(self, pp, puck, my_paddle, opponent_paddle):
        if self.prepare_to_send(pp, puck.rect.x, puck.rect.y):
            # Check if a collision with my paddle occurs
            if self.detect_collision(puck, my_paddle):
                self.collision_detected = True
                self.opponent_collision_detected = False  # Reset opponent flag

            # Check if the opponent collides to stop sending
            if self.opponent_collision(puck, opponent_paddle):
                self.opponent_collision_detected = True
                self.collision_detected = False  # Stop sending from this side

            # If collision was detected, keep sending puck updates
            if self.collision_detected:
                if self.client:
                    try:
                        position_data = json.dumps({'puck_x': puck.rect.x, 'puck_y': puck.rect.y})
                        message = position_data.encode(FORMAT)
                        send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
                        self.client.send(send_length)
                        self.client.send(message)
                        # print(f'Sending puck position: x={puck.rect.x}, y={puck.rect.y}')
                    except Exception as e:
                        print(f'Failed to send puck position data: {e}')
                        self.client.close()
                        self.client = None

    # reset the puck's position; its x and y values and its velocity
    def reset_position(self):
        self.rect.center = self.start_pos
        self.velocity = Vector(0, 0)  # Reset velocity

    # draw the puck on the board
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


# manages the pvp game, handling the game loop, collisions, and goals scored
class Pvp:
    def __init__(self, surface, player_pos, opponent_pos, client, username, player_id, trophies, arena, disconnect):
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
        self.player_score = 0
        self.opponent_score = 0
        self.arena = arena
        self.player_paddle = None
        self.disconnect = False

        self.opponent_paddle = Paddle(self.opp_pos, self.RED, 37, 'right', speed=4, power=0.00000000001,
                                      client=self.client)

        self.puck = Puck(self.puck_pos, self.WHITE, 30, client=self.client)

        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()

    # establishes a connection to the database allowing for SQL commands
    def runsql(self, *args):
        conn = sqlite3.connect('air_hockey.db')
        conn.execute('PRAGMA foreign_keys = 1')
        cursor = conn.cursor()
        if len(args) == 1:
            cursor.execute(args[0])
        else:
            cursor.execute(args[0], args[1])
        conn.commit()
        return cursor.fetchall()

    # function to check whether a goal has been scored

    def check_goal(self):

        # if your goal is left check whether you scored it's the opponents goal
        if self.player_position == 1:
            # print('checking goal')
            if self.puck.rect.right >= 1065 and 270 <= self.puck.rect.centery <= 430:
                self.display_countdown()
                self.player_score += 1
                print('player scored')
                return 'goal'
            elif self.puck.rect.left <= 0 and 270 <= self.puck.rect.centery <= 430:
                self.display_countdown()
                self.opponent_score += 1
                print('opponent scored')
                return 'goal'

        # vice versa if you're on the right side
        if self.player_position == 2:
            # print('checking goal')
            # print(self.puck.rect.left)
            if self.puck.rect.left <= 25 and 270 <= self.puck.rect.centery <= 430:
                self.display_countdown()
                self.player_score += 1
                print('player scored')
                return 'goal'
            elif self.puck.rect.right > 1090 and 270 <= self.puck.rect.centery <= 430:
                self.display_countdown()
                self.opponent_score += 1
                print('opponent scored')
                return 'goal'

    # draw text unto the board(player_score and opponent_score)
    def draw_text(self, surface, text, font, color, pos):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, pos)

    # handles the collisions between the paddle, opponent paddles and the puck's
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

        if puck.rect.colliderect(self.opponent_paddle.rect):
            normal = Vector(puck.rect.centerx - self.opponent_paddle.rect.centerx,
                            puck.rect.centery - self.opponent_paddle.rect.centery).normalise()
            relative_velocity = puck.velocity - self.opponent_paddle.velocity
            velocity_along_normal = relative_velocity.dot(normal)

            # reflect the puck's velocity along the normal
            if velocity_along_normal < 0:  # Ensure we only reflect if moving towards the paddle
                puck.velocity = puck.velocity - normal * (2 * velocity_along_normal)

            # increase puck velocity based on paddle power
            puck.velocity += normal * self.opponent_paddle.power  # Adjust puck velocity by paddle power

            # move puck out of collision
            while puck.rect.colliderect(self.opponent_paddle.rect):
                puck.rect.x += normal.x
                puck.rect.y += normal.y

    # displays the game winner on screen
    def display_winner(self, surface, text):
        font = pygame.font.Font('../LEMONMILK-Medium.otf', 40)
        text_surf = font.render(text, True, BLACK)
        surface.blit(text_surf, (200, 150))
        pygame.display.flip()
        pygame.time.delay(2000)

    # listens for any incoming messages from the server and updates game objects
    def listen_for_server_messages(self):
        while self.client:  # Only run if client is not None
            try:
                msg = self.client.recv(1024).decode(FORMAT)
                if not msg:
                    print("Server closed connection.")
                    break  # Stop the loop if no message received

                print(f"Received message: {msg}")

                if msg == 'od':  # Opponent Disconnected
                    print('Opponent disconnected, triggering win condition.')
                    self.win()
                    break  # Exit the loop to stop listening

                # Process JSON messages
                try:
                    position_data = json.loads(msg)
                    if 'x' in position_data and 'y' in position_data:
                        self.opponent_paddle.update_opponent_position(position_data['x'], position_data['y'])
                    elif 'puck_x' in position_data and 'puck_y' in position_data:
                        self.puck.update_puck_position(position_data['puck_x'], position_data['puck_y'])
                except json.JSONDecodeError:
                    print("Error decoding JSON message.")

            except (OSError, ConnectionResetError):
                print("Connection lost. Stopping listener.")
                break  # Stop the loop if connection is lost

            except AttributeError:  # Handle case where self.client is None
                print("Client socket closed, stopping listener.")
                break

        print("Listener thread stopped.")

    # handles a player's victory by updating the database and displaying the results, also disconnects that player from the server and sending them back to the menu
    def win(self):
        print('You won')

        trophies_won = random.randint(27, 33)  # Random trophies earned

        if self.client:
            try:
                # Send disconnect message to server
                self.send_message(DISCONNECT_MESSAGE)

                # Display win message
                font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
                font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
                win_text = font1.render(f'You have won!!!', True, BLACK)
                result_text = font2.render(f'You have gained {trophies_won} trophies', True, BLACK)
                surface.blit(win_text, (450, 300))
                surface.blit(result_text, (435, 350))
                pygame.display.flip()
                pygame.time.delay(1000)

                # Update trophies in database
                query = '''
                    UPDATE tblPlayerStats
                    SET totalTrophies = totalTrophies + ?,
                        pvpWins = pvpWins + 1
                    WHERE playerId = ?
                '''
                values = (trophies_won, self.player_id)
                self.runsql(query, values)
                print(f'Player trophies and win count updated: {trophies_won}')

            except Exception as e:
                print(f'Error handling win: {e}')

            finally:
                # Stop the listening thread safely
                self.client = None  # This will stop listen_for_server_messages

                pygame.time.delay(500)  # Short delay for smooth transition

        return trophies_won

    # handles a player's loss by updating the database and displaying the results, also disconnects that player from the server and sending them back to the menu
    def loss(self):
        print('You lost')

        # Determine trophies lost based on arena level
        if self.arena == 1:
            trophies_lost = random.randint(5, 8)
        elif self.arena == 2:
            trophies_lost = random.randint(10, 13)
        elif self.arena == 3:
            trophies_lost = random.randint(15, 18)
        else:
            trophies_lost = 0

        if self.client:
            try:
                # Send disconnect message to server
                self.send_message(DISCONNECT_MESSAGE)

                # Display loss message
                font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
                font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
                loss_text = font1.render(f'You have lost!!!', True, BLACK)
                result_text = font2.render(f'You have lost {trophies_lost} trophies', True, BLACK)
                surface.blit(loss_text, (450, 300))
                surface.blit(result_text, (435, 350))
                pygame.display.flip()
                pygame.time.delay(1000)

                # Update trophies in database
                if self.trophies >= 0:
                    query = '''
                        UPDATE tblPlayerStats
                        SET totalTrophies = totalTrophies - ?,
                            pvpLosses = pvpLosses + 1
                        WHERE playerId = ?
                    '''
                    values = (trophies_lost, self.player_id)
                    self.runsql(query, values)

                if self.trophies < 0:
                    query = '''
                        UPDATE tblPlayerStats
                        SET totalTrophies = 0
                        WHERE playerId = ?
                    '''
                    values = (self.player_id,)
                    self.runsql(query, values)

            except Exception as e:
                print(f'Error handling loss: {e}')

            finally:
                # Stop the listening thread safely
                self.client = None  # This will stop listen_for_server_messages

                pygame.time.delay(500)

        return trophies_lost

    # displays a 3-second countdown before restarting the game
    def display_countdown(self):
        font = pygame.font.Font(None, 120)  # Set a font size for the countdown
        for i in range(3, 0, -1):  # Countdown from 3 to 1
            self.surface.fill(BLACK)  # Clear the screen
            text = font.render(str(i), True, WHITE)  # Render the countdown number
            text_rect = text.get_rect(center=(surface_width // 2, surface_height // 2))
            self.surface.blit(text, text_rect)  # Draw the number on the screen
            pygame.display.flip()  # Update the display
            pygame.time.delay(1000)  # Wait for 1 second

    # draws the countdown timer unto the screen
    def draw_timer(self, surface, time_remaining):
        font = pygame.font.Font(None, 42)
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_text = f"{minutes:02}:{seconds:02}"
        timer_surface = font.render(timer_text, True, WHITE)
        surface.blit(timer_surface, (surface_width // 2 - 50, 20))  # Position at the top centre

    # displays the player and opponent scores
    def display_info(self):
        font = pygame.font.Font('../LEMONMILK-Bold.otf', 24)

        if self.player_position == 1:
            # set variables for both player and opponent scores
            display_player_score = font.render(f'{self.player_score}', True, WHITE)
            display_opponent_score = font.render(f'{self.opponent_score}', True, WHITE)

            # blit those variables unto screen
            surface.blit(display_player_score, (475, 15))
            surface.blit(display_opponent_score, (625, 15))

        else:
            # vice-versa if player_position == 2
            display_player_score = font.render(f'{self.player_score}', True, WHITE)
            display_opponent_score = font.render(f'{self.opponent_score}', True, WHITE)

            surface.blit(display_opponent_score, (475, 15))
            surface.blit(display_player_score, (625, 15))

    # sends a message to the server
    def send_message(self, msg):
        if self.client:
            message = msg.encode(FORMAT)
            send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
            self.client.send(send_length)
            self.client.send(message)
            # self.client.send()

    # runs the main game loop, handling game logic, rendering, and the networking
    def show_screen(self):
        global sudden_death_active, time_remaining
        max_score = 1

        font = pygame.font.Font('../LEMONMILK-Bold.otf', 24)

        # Initialize objects
        # Proper start positions
        player1_start_position = (150, 325)
        opponent_start_position = (950, 325)

        # Conditional initialization based on player position
        if self.player_position == 1:
            print('I AM PLAYER 1')
            self.player_paddle = Paddle(player1_start_position, self.BLUE, 37, 'left', speed=6, power=7,
                                        client=self.client)
            self.opponent_paddle = Paddle(opponent_start_position, self.RED, 37, 'right', speed=6, power=7,
                                          client=self.client)

        else:
            print('I AM PLAYER 2')
            self.player_position = 2
            self.player_paddle = Paddle(opponent_start_position, self.RED, 37, 'right', speed=6, power=7,
                                        client=self.client)
            self.opponent_paddle = Paddle(player1_start_position, self.BLUE, 37, 'left', speed=6, power=7,
                                          client=self.client)

        puck_start_position = (surface_width // 2, surface_height // 2)
        # puck = Puck(puck_start_position, self.WHITE, 30, client=self.client)

        board = neonBoard(1100, 650)
        # player_paddle.set_puck(self.puck)

        # print(self.player_username)

        clock = pygame.time.Clock()

        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()

        while self.opponent_score != max_score and self.player_score != max_score:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            time_delta = clock.tick(120) / 2  # Time passed in seconds
            time_remaining -= time_delta

            # Handle end of timer
            if time_remaining <= 0:
                if not sudden_death_active:
                    if self.player_score > self.opponent_score:
                        self.win()
                        return
                    elif self.opponent_score > self.player_score:
                        self.loss()
                        return
                    else:
                        sudden_death_active = True
                        self.puck.reset_position()
                        self.player_paddle.reset_position()
                        self.opponent_paddle.reset_position()
                        self.display_countdown()
                        self.display_winner(surface, "SUDDEN DEATH!!!")
                        time_remaining = sudden_death_duration  # Add sudden death time
                else:
                    self.loss()
                    return

            # Update game objects
            self.player_paddle.update(events)
            self.puck.update()

            # Check for goals
            score = self.check_goal()
            if score == 'goal':
                self.puck.reset_position()
                self.player_paddle.reset_position()
                self.opponent_paddle.reset_position()
            self.player_paddle.send_position_data()
            self.puck.position_data(self.player_position, self.puck, self.player_paddle, self.opponent_paddle)
            # print(f"Puck rendering at: x={self.puck.rect.x}, y={self.puck.rect.y}")

            # Handle collisions
            self.handle_collisions(self.puck, self.player_paddle)

            # Update and draw the board
            board.update()
            board.draw(self.surface)

            # Draw the game objects
            self.player_paddle.draw(self.surface)
            self.opponent_paddle.draw(self.surface)  # Draw opponent paddle
            # print(f'puck pos before being drawn: x={self.puck.rect.x}, y={self.puck.rect.y}') # Debug
            self.puck.draw(self.surface)
            # print(f'puck pos after being drawn: x={self.puck.rect.x}, y={self.puck.rect.y}') # Debug

            self.display_info()
            self.draw_timer(surface, time_remaining)

            pygame.display.flip()
            clock.tick(120)

        if self.player_score >= max_score:
            self.win()
            print('returned end')
            return 'game ended'

        if self.opponent_score >= max_score:
            self.loss()
            print('RETURNED END')
            return 'game ended'
