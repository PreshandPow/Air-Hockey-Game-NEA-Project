import pygame
import sys
import sqlite3
from PIL import Image, ImageSequence
from neon_arena import neonBoard
from underwater_board import UnderwaterArena
import random

# Initialize Pygame
pygame.display.init()
pygame.font.init()

# Set up the display
surface_width, surface_height = 1100, 650
surface = pygame.display.set_mode((surface_width, surface_height))
pygame.display.set_caption('Air Hockey PVE!')

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

# AI difficulty levels
EASY = 1
NORMAL = 2
HARD = 3
difficulty = None

game_duration = 180  # 3 minutes in seconds
sudden_death_duration = 60  # 1 minute in seconds
time_remaining = game_duration
sudden_death_active = False
clock = pygame.time.Clock()  # Ensure smooth timing updates

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
    def __init__(self, start_pos, color, radius, side, speed=6, power=1):  # Increased power
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # paddle outline
        pygame.draw.circle(self.image, BLACK, (radius, radius), 21)  # black centre of the paddle
        self.rect = self.image.get_rect(center=start_pos)  # get the rect of the paddle
        self.color = color  # colour of paddle
        self.radius = radius  # radius/size of paddle
        self.holding = False  # if the paddle is being held/clicked on
        self.side = side  # the edges of the paddle
        self.velocity = Vector()  # call the vector function
        self.start_pos = start_pos  # the start position of the paddle at the beginning of every round
        self.speed = speed  # the speed of the paddle
        self.power = power  # the power at which the paddle hits the puck
        self.intelligence = 1  # the intelligence factor for the AI
        self.puck = None

    def set_puck(self, puck):
        self.puck = puck

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
        # in order for the opponent_paddle to move is calls the ai_move() method
        else:  # AI paddle
            self.ai_move()

        # restrict paddle movement, so it can't come off the board
        if self.side == 'left':
            if self.rect.right > surface_width // 2:
                self.rect.right = surface_width // 2
            if self.rect.left < 0:
                self.rect.left = 0
        else:
            if self.rect.left < surface_width // 2:
                self.rect.left = surface_width // 2

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

    # AI for the opponent_paddle
    def ai_move(self):
        puck_center = self.puck.rect.center  # This may return a tuple
        paddle_center = self.rect.center

        # Predict the puck's future position only if it's moving toward the AI
        predicted_puck = None
        if self.puck.velocity.x > 0:  # Puck is moving toward the AI
            predicted_puck = self.predict_puck_position()

        # Determine the target position: either prediction or current puck position
        target_position = predicted_puck if predicted_puck else Vector(puck_center[0], puck_center[1])

        # Debugging: Print the target position to ensure correctness
        print(f"Target position: {target_position} (type: {type(target_position)})")

        # Defensive mode: If the puck is on the player's side
        if self.puck.rect.centerx < surface_width // 2:
            # Move back to a defensive position near the goal
            goal_position = (3 * surface_width // 4, surface_height // 2)
            if paddle_center[0] < goal_position[0]:
                self.rect.centerx += self.speed
            elif paddle_center[0] > goal_position[0]:
                self.rect.centerx -= self.speed

            if paddle_center[1] < goal_position[1]:
                self.rect.centery += self.speed
            elif paddle_center[1] > goal_position[1]:
                self.rect.centery -= self.speed

        # Offensive mode: If the puck is on the AI's side
        else:
            # Move toward the target position (predicted or current)
            if paddle_center[0] < target_position.x:  # Ensure target_position is a Vector
                self.rect.centerx += self.speed
            elif paddle_center[0] > target_position.x:
                self.rect.centerx -= self.speed

            if paddle_center[1] < target_position.y:
                self.rect.centery += self.speed
            elif paddle_center[1] > target_position.y:
                self.rect.centery -= self.speed

        # Ensure the paddle doesn't leave its half of the field
        if self.rect.left < surface_width // 2:
            self.rect.left = surface_width // 2
        if self.rect.right > surface_width:
            self.rect.right = surface_width
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > surface_height:
            self.rect.bottom = surface_height

    def predict_puck_position(self):
        # Use Vector for calculations
        future_puck = Vector(self.puck.rect.centerx, self.puck.rect.centery)
        velocity = Vector(self.puck.velocity.x, self.puck.velocity.y)

        # Stop predicting if the puck is stationary
        if velocity.length() == 0:
            return future_puck  # Return Vector

        # Predict puck's position after a small time step
        for _ in range(10):  # Adjust the range for more/less prediction steps
            future_puck += velocity
            # Simulate bouncing off top/bottom walls
            if future_puck.y <= 0 or future_puck.y >= surface_height:
                velocity.y *= -1

        return future_puck  # Return Vector


# the class for the puck taking in 3 attributes
class Puck(pygame.sprite.Sprite):
    def __init__(self, start_pos, color, radius):
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # the puck
        self.rect = self.image.get_rect(center=start_pos)  # the puck's rect
        self.color = color  # the colour of the puck
        self.radius = radius  # the radius/size of the puck
        self.velocity = Vector(0, 0)  # initial velocity slightly increased
        self.friction = 0.98  # the friction so the puck slows down over time
        self.max_speed = 50  # the maximum speed which the puck can move at
        self.min_speed = 0  # the minimum speed the puck can move at
        self.start_pos = start_pos  # the starting position of the puck

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

    # reset the puck's position/its x and y values and its velocity
    def reset_position(self):
        self.rect.center = self.start_pos
        self.velocity = Vector(0, 0)  # Reset velocity

    # draw the puck on the board
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


# the class for the hockey board it takes in 2 attributes

class Pve:
    def __init__(self, surface, Session_info):
        self.surface = surface
        self.data_store = Session_info
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
    def check_goal(self, puck, player_score, opponent_score, player_paddle, opponent_paddle):
        if puck.rect.left <= 0 and 250 <= puck.rect.centery <= 400:
            opponent_score += 1
            if sudden_death_active:  # End game in sudden death
                self.display_winner(surface, "Computer Wins!")
                return player_score, opponent_score
            self.display_countdown()
            puck.reset_position()
            player_paddle.reset_position()
            opponent_paddle.reset_position()

        elif puck.rect.right >= surface_width and 250 <= puck.rect.centery <= 400:
            player_score += 1
            if sudden_death_active:  # End game in sudden death
                self.display_winner(surface, "Player Wins!")
                return player_score, opponent_score
            self.display_countdown()
            puck.reset_position()
            player_paddle.reset_position()
            opponent_paddle.reset_position()

        return player_score, opponent_score

    def display_countdown(self):
        """Displays a 3-second countdown on the screen."""
        font = pygame.font.Font(None, 120)  # Set a font size for the countdown
        for i in range(3, 0, -1):  # Countdown from 3 to 1
            self.surface.fill(BLACK)  # Clear the screen
            text = font.render(str(i), True, WHITE)  # Render the countdown number
            text_rect = text.get_rect(center=(surface_width // 2, surface_height // 2))
            self.surface.blit(text, text_rect)  # Draw the number on the screen
            pygame.display.flip()  # Update the display
            pygame.time.delay(1000)  # Wait for 1 second

        # it checks whether the puck.rect.left/.right collides with either goal and will update both player's scores and rest the puck's position

    # draw text unto the board(player_score and opponent_score)
    def draw_text(self, surface, text, font, color, pos):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, pos)

    # function to calculate what difficulty the player has chosen
    def difficulty_selection(self):
        def draw_gradient(self, surface, start_color, end_color):
            # Get the dimensions of the surface
            width, height = surface.get_size()

            # Calculate color change per pixel
            delta_r = (end_color[0] - start_color[0]) / width
            delta_g = (end_color[1] - start_color[1]) / width
            delta_b = (end_color[2] - start_color[2]) / width

            for x in range(width):
                # Calculate the new color for this position
                new_color = (
                    int(start_color[0] + delta_r * x),
                    int(start_color[1] + delta_g * x),
                    int(start_color[2] + delta_b * x)
                )
                pygame.draw.line(surface, new_color, (x, 0), (x, height))

        def draw(surface):
            # Define gradient colors
            start_color = OUTER_SPACE
            end_color = RICH_BLACK

            # Fill the surface with a gradient
            draw_gradient(self, surface, start_color, end_color)

        global difficulty
        font = pygame.font.Font('../LEMONMILK-Medium.otf', 74)
        font2 = pygame.font.Font('../LEMONMILK-Medium.otf', 40)
        easy_text_colour = GREEN
        easy_text = font.render('Easy', True, easy_text_colour)
        easy_info = font2.render('Win: gain 2 trophies\nLoss: lose 0 trophies', True, WHITE)
        easy_text_rect = easy_text.get_rect()
        normal_text_colour = 'white'
        normal_text = font.render('Normal', True, normal_text_colour)
        normal_info = font2.render('Win: gain 5 trophies\nLoss: Loss: lose 3 trophies', True, WHITE)
        hard_text_colour = RED
        hard_text = font.render('Hard', True, hard_text_colour)
        hard_info = font2.render('Win: gain 10 trophies\nLoss: lose 7 trophies', True, WHITE)
        return_button = pygame.transform.scale(pygame.image.load('../return button.png'), (125, 125))
        return_button_rect = return_button.get_rect()

        while True:
            surface.fill(WHITE)
            draw(surface)
            self.draw_text(surface, "Select Difficulty", font, BLACK, (50, 15))
            surface.blit(easy_text, (75, 150))
            surface.blit(normal_text, (75, 300))
            surface.blit(hard_text, (75, 450))
            surface.blit(return_button, (900, 40))
            pygame.display.flip()
            eventss = pygame.event.get()
            mouse_position = pygame.mouse.get_pos()
            return_button = pygame.transform.scale((pygame.image.load('../return button.png')), (75, 75))
            for event in eventss:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                surface.blit(return_button, (500, 100))
                if 75 <= mouse_position[0] <= 275 and 150 <= mouse_position[1] <= 225:
                    easy_text_colour = CERULEAN
                    easy_text = font.render('Easy', True, easy_text_colour)
                    surface.blit(easy_text, (400, 250))
                    surface.blit(easy_info, (400, 300))
                else:
                    easy_text_colour = GREEN
                    easy_text = font.render('Easy', True, easy_text_colour)
                    surface.blit(easy_text, (400, 250))
                if 75 <= mouse_position[0] <= 425 and 300 <= mouse_position[1] <= 375:
                    normal_text_colour = CERULEAN
                    normal_text = font.render('Normal', True, normal_text_colour)
                    surface.blit(normal_text, (75, 300))
                    surface.blit(normal_info, (400, 300))
                else:
                    normal_text_colour = 'grey'
                    normal_text = font.render('Normal', True, normal_text_colour)
                    surface.blit(normal_text, (75, 300))
                if 75 <= mouse_position[0] <= 275 and 475 <= mouse_position[1] <= 550:
                    hard_text_colour = CERULEAN
                    hard_text = font.render('Hard', True, hard_text_colour)
                    surface.blit(hard_text, (75, 450))
                    surface.blit(hard_info, (400, 300))
                else:
                    hard_text_colour = RED
                    hard_text = font.render('Hard', True, hard_text_colour)
                    surface.blit(hard_text, (75, 450))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 75 <= mouse_position[0] <= 275 and 150 <= mouse_position[1] <= 225:
                        return EASY
                    elif 75 <= mouse_position[0] <= 425 and 300 <= mouse_position[1] <= 375:
                        return NORMAL
                    elif 75 <= mouse_position[0] <= 275 and 475 <= mouse_position[1] <= 550:
                        return HARD
                    elif 900 <= mouse_position[0] <= 975 and 40 <= mouse_position[1] <= 105:
                        return 'return'

    def handle_collisions(self, puck, paddle):
        if puck.rect.colliderect(paddle.rect):
            normal = Vector(puck.rect.centerx - paddle.rect.centerx,
                            puck.rect.centery - paddle.rect.centery).normalise()
            relative_velocity = puck.velocity - paddle.velocity
            velocity_along_normal = relative_velocity.dot(normal)
            print(velocity_along_normal)

            # reflect the puck's velocity along the normal
            if velocity_along_normal < 0:  # Ensure we only reflect if moving towards the paddle
                puck.velocity = puck.velocity - normal * (2 * velocity_along_normal)

            # increase puck velocity based on paddle power
            puck.velocity += normal * paddle.power  # Adjust puck velocity by paddle power

            # move puck out of collision
            while puck.rect.colliderect(paddle.rect):
                puck.rect.x += normal.x
                puck.rect.y += normal.y

    def select_difficulty(self, opponent_start_position):
        mouse_pos = pygame.mouse.get_pos()
        difficulty = self.difficulty_selection()
        if difficulty == 'return':
            return 'return'
        if difficulty == EASY:
            opponent_paddle = Paddle(opponent_start_position, RED, 37, 'right', speed=5, power=10)
            opponent_paddle.intelligence = 0.5
        elif difficulty == NORMAL:
            opponent_paddle = Paddle(opponent_start_position, RED, 37, 'right', speed=8, power=15)
            opponent_paddle.intelligence = 5
        elif difficulty == HARD:
            opponent_paddle = Paddle(opponent_start_position, RED, 37, 'right', speed=15, power=50)
            opponent_paddle.intelligence = 10000000
        else:
            opponent_paddle = Paddle(opponent_start_position, RED, 37, 'right', speed=4, power=1.7)
            opponent_paddle.intelligence = 1
        return opponent_paddle, difficulty

    # the function to show the winner of the game

    def display_winner(self, surface, text):
        font = pygame.font.Font('../LEMONMILK-Medium.otf', 62)
        text_surf = font.render(text, True, WHITE)
        surface.blit(text_surf, (200, 150))
        pygame.display.flip()
        pygame.time.delay(2000)

    def easy_win(self, surface):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        if not id:
            raise ValueError("Player ID not found in data store")
        fetch_wins_trophies = '''
        SELECT totalTrophies,
        pveWins
        FROM tblPlayerStats
        WHERE playerId = ?
        '''
        values = (id,)
        result = self.runsql(fetch_wins_trophies, values)

        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies + 5,
        pveWins = pveWins + 1
        WHERE playerId = ?
        '''
        values = (id,)
        self.runsql(query, values)
        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        win = font1.render(f'{username} has won!!!', True, WHITE)
        result = font2.render('You have gained 5 trophies', True, WHITE)
        surface.blit(win, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def easy_loss(self):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        trophies = self.data_store.get_data("trophies")
        if not id:
            raise ValueError("Player ID not found in data store")
        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies - 2,
        pveLosses = pveLosses + 1
        WHERE playerId = ?
        '''

        values = (id,)
        self.runsql(query, values)

        if trophies < 0 :
            print('set trophies to 0')
            query2 = '''
                UPDATE tblPlayerStats
                SET totalTrophies = 0
                WHERE playerId = ?        
            '''

            values = (id,)
            self.runsql(query2, values)

        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        loss = font1.render(f'{username} has lost!!!', True, WHITE)
        result = font2.render('You have lost 2 trophies', True, WHITE)
        surface.blit(loss, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def normal_win(self, surface):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        if not id:
            raise ValueError("Player ID not found in data store")
        fetch_wins_trophies = '''
        SELECT totalTrophies,
        pveWins
        FROM tblPlayerStats
        WHERE playerId = ?
        '''
        values = (id,)
        result = self.runsql(fetch_wins_trophies, values)

        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies + 10,
        pveWins = pveWins + 1
        WHERE playerId = ?
        '''
        values = (id,)
        self.runsql(query, values)
        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        win = font1.render(f'{username} has won!!!', True, WHITE)
        result = font2.render('You have gained 10 trophies', True, WHITE)
        surface.blit(win, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def normal_loss(self):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        trophies = self.data_store.get_data("trophies")
        if not id:
            raise ValueError("Player ID not found in data store")
        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies - 5,
        pveLosses = pveLosses + 1
        WHERE playerId = ?
        '''

        values = (id,)
        self.runsql(query, values)

        if trophies < 0:
            print('set trophies to 0')
            query2 = '''
                UPDATE tblPlayerStats
                SET totalTrophies = 0
                WHERE playerId = ?        
            '''

            values = (id,)
            self.runsql(query2, values)

        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        loss = font1.render(f'{username} has lost!!!', True, WHITE)
        result = font2.render('You have lost 5 trophies', True, WHITE)
        surface.blit(loss, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def hard_win(self, surface):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        if not id:
            raise ValueError("Player ID not found in data store")
        fetch_wins_trophies = '''
        SELECT totalTrophies,
        pveWins
        FROM tblPlayerStats
        WHERE playerId = ?
        '''
        values = (id,)
        result = self.runsql(fetch_wins_trophies, values)

        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies + 15,
        pveWins = pveWins + 1
        WHERE playerId = ?
        '''
        values = (id,)
        self.runsql(query, values)
        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        win = font1.render(f'{username} has won!!!', True, WHITE)
        result = font2.render('You have gained 15 trophies', True, WHITE)
        surface.blit(win, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def hard_loss(self):
        username = self.data_store.get_data("username")
        id = self.data_store.get_data("id")
        trophies = self.data_store.get_data('trophies')
        if not id:
            raise ValueError("Player ID not found in data store")
        query = '''
        UPDATE tblPlayerStats
        SET totalTrophies = totalTrophies - 15,
        pveLosses = pveLosses + 1
        WHERE playerId = ?
        '''

        values = (id,)
        self.runsql(query, values)

        if trophies < 0:
            print('set trophies to 0')
            query2 = '''
                UPDATE tblPlayerStats
                SET totalTrophies = 0
                WHERE playerId = ?        
            '''

            values = (id,)
            self.runsql(query2, values)

        font1 = pygame.font.Font('../LEMONMILK-Bold.otf', 38)
        font2 = pygame.font.Font('../LEMONMILK-Light.otf', 24)
        loss = font1.render(f'{username} has lost!!!', True, WHITE)
        result = font2.render('You have lost 15 trophies', True, WHITE)
        surface.blit(loss, (400, 150))
        surface.blit(result, (375, 200))
        pygame.display.flip()
        pygame.time.delay(1000)

    def draw_timer(self, surface, time_remaining):
        """Draws the countdown timer on the screen."""
        font = pygame.font.Font(None, 42)
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_text = f"{minutes:02}:{seconds:02}"
        timer_surface = font.render(timer_text, True, WHITE)
        surface.blit(timer_surface, (surface_width // 2 - 50, 20))  # Position at the top centre

    def show_screen(self):
        # Initial Scores
        global time_remaining, sudden_death_active
        player_score = 0
        opponent_score = 0
        max_score = 2

        font = pygame.font.Font(None, 42)
        display_player_name = font.render('Player', True, BLACK)
        display_player_score = font.render(f'{player_score}', True, BLACK)
        display_opponent_name = font.render('Computer', True, BLACK)
        display_opponent_score = font.render(f'{opponent_score}', True, BLACK)

        # mouse_pos = pygame.mouse.get_pos()

        # Initialize objects
        player_start_position = (150, 325)
        opponent_start_position = (950, 325)

        player_paddle = Paddle(player_start_position, BLUE, 37, 'left', speed=12,
                               power=5)  # Increased player paddle power
        difficulty_result = self.select_difficulty(opponent_start_position)
        if difficulty_result == 'return':
            return 'return'
        else:
            opponent_paddle = difficulty_result[0]
        puck_start_position = (surface_width // 2, surface_height // 2)
        print(difficulty_result[1])
        puck = Puck(puck_start_position, WHITE, 30)

        # board = neonBoard(1100, 650)

        arena = self.data_store.get_data('arena')

        if arena == 1:
            board = neonBoard(1100, 650)

        elif arena == 2:
            board = UnderwaterArena(1100, 650)

        else:
            print('cant get arena')

        player_paddle.set_puck(puck)
        opponent_paddle.set_puck(puck)

        clock = pygame.time.Clock()

        while opponent_score < max_score and player_score < max_score:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Calculate elapsed time
            time_delta = clock.tick(120) / 100  # Time passed in seconds
            time_remaining -= time_delta

            # Handle end of timer
            if time_remaining <= 0:
                if not sudden_death_active:
                    if player_score > opponent_score:
                        if difficulty_result[1] == EASY:
                            self.easy_win(surface)
                        if difficulty_result[1] == NORMAL:
                            self.normal_win(surface)
                        if difficulty_result[1] == HARD:
                            self.hard_win(surface)
                        return
                    elif opponent_score > player_score:
                        if difficulty_result[1] == EASY:
                            self.easy_loss()
                        if difficulty_result[1] == NORMAL:
                            self.normal_loss()
                        if difficulty_result[1] == HARD:
                            self.hard_loss()
                        return
                    else:
                        sudden_death_active = True
                        puck.reset_position()
                        player_paddle.reset_position()
                        opponent_paddle.reset_position()
                        self.display_countdown()
                        self.display_winner(surface, "SUDDEN DEATH!!!")
                        time_remaining = sudden_death_duration  # Add sudden death time
                else:
                    if difficulty_result[1] == EASY:
                        self.easy_loss()
                    if difficulty_result[1] == NORMAL:
                        self.normal_loss()
                    if difficulty_result[1] == HARD:
                        self.hard_loss()
                    return

            mouse_pos = pygame.mouse.get_pos()

            # Update game objects
            player_paddle.update(events)
            opponent_paddle.update(events)
            puck.update()

            # Handle collisions
            self.handle_collisions(puck, player_paddle)
            self.handle_collisions(puck, opponent_paddle)

            # Check for goals
            player_score, opponent_score = self.check_goal(puck, player_score, opponent_score, player_paddle,
                                                           opponent_paddle)
            display_player_score = font.render(f'{player_score}', True, WHITE)
            display_opponent_score = font.render(f'{opponent_score}', True, WHITE)

            # Update and draw the board
            board.update()
            board.draw(surface)

            # Draw the rest of the game objects
            player_paddle.draw(surface)
            opponent_paddle.draw(surface)
            puck.draw(surface)

            # Display scores
            surface.blit(display_player_score, (60, 20))
            surface.blit(display_opponent_score, (950, 20))

            self.draw_timer(surface, time_remaining)

            pygame.display.flip()
            clock.tick(120)

            if player_score >= max_score:
                if difficulty_result[1] == EASY:
                    self.easy_win(surface)
                if difficulty_result[1] == NORMAL:
                    self.normal_win(surface)
                if difficulty_result[1] == HARD:
                    self.hard_win(surface)

            if opponent_score >= max_score:
                if difficulty_result[1] == EASY:
                    self.easy_loss()
                if difficulty_result[1] == NORMAL:
                    self.normal_loss()
                if difficulty_result[1] == HARD:
                    self.hard_loss()