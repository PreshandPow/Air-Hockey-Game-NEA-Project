import pygame, bcrypt, sqlite3
from loading_screen import *


# This class is used to crate the username and password input box’s actions for when the user either wants to create
# an account or log into an existing account. Note, this class does not actually create the input boxes,
# it only crates the actions and how the input boxes will actually work.
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.MINT_GREEN = (194, 239, 235)
        self.CERULEAN = (0, 126, 167)
        self.rect = pygame.Rect(x, y, w, h)
        self.color = self.CERULEAN
        self.text = text
        self.txt_surface = pygame.font.Font('../LEMONMILK-Light.otf', 18).render(text, True, self.BLACK)
        self.active = False

    # This function handles user interaction with a username and password input box. When clicked on, it toggles its
    # active state and when a key is pressed,and it is active, it will update what key is pressed.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the color of the input box.
            self.color = self.MINT_GREEN if self.active else self.CERULEAN
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print(self.text)  # print the text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = pygame.font.Font('../Roboto-BoldCondensed.ttf', 18).render(self.text, True,
                                                                                              self.BLACK)

    # This function will display the text stored in the input box and will update it in real time including if the
    # backspace is pressed as well.
    def draw(self, surface):
        # Blit the text.
        surface.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the rect.
        pygame.draw.rect(surface, self.color, self.rect, 2)


# This class is used to store the user’s session information. E.g., their username, password and user ID.
class SessionInfo:
    def __init__(self):
        self.data = {}

    # This function is used in order to add data into the class. For example, when the user finishes creating their
    # account or logging in, it runs code which will fetch their user ID using information provided and store it in
    # the class by calling “self.data_store.add_data ()”
    def add_data(self, key, value):
        self.data[key] = value

    # This function is used to go and retrieve the data which has been added into SessionInfo. The data is retrieved
    # why using “self.data_store.get_data ()”. In the parenthesis you would include the key for which the data is
    # stored in. For example, the key “username” would include the user’s username (e.g. FadedPigeon47)
    def get_data(self, key):
        return self.data.get(key, None)


# This class will crate the input boxes and display for signing in and creating an account. It creates the username
# and password input boxes and allows them to be functional and interacted with. It will also hash a newly created
# user’s password and store it in a database.
class signIn:
    def __init__(self, surface):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.MINT_GREEN = (194, 239, 235)
        self.CERULEAN = (0, 126, 167)
        self.surface = surface

        # Create input boxes for sign up
        self.input_boxes_sign_up = [InputBox(380, 270, 340, 32), InputBox(380, 410, 340, 32),
                                    InputBox(380, 500, 340, 32)]
        # Create input boxes for log in
        self.input_boxes_log_in = [InputBox(380, 270, 340, 32), InputBox(380, 410, 340, 32)]

        self.data_store = SessionInfo()

    # This function will return all current information stored in SessionInfo
    def get_session_data(self):
        return self.data_store

    # This function will create the sign-in page’s background which is a gradient of a blue and purple like colour.
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

    def draw(self, surface):
        # Define gradient colors
        start_color = (110, 164, 191)
        end_color = (65, 51, 122)

        # Fill the surface with a gradient
        self.draw_gradient(surface, start_color, end_color)

    def draw_buttons(self, log_in_color, sign_up_color):
        # Background
        pygame.draw.rect(self.surface, self.WHITE, (350, 50, 400, 550), border_radius=25)
        # Log in button
        pygame.draw.rect(self.surface, log_in_color, (390, 125, 150, 50), border_radius=10)
        # Sign up button
        pygame.draw.rect(self.surface, sign_up_color, (565, 125, 150, 50), border_radius=10)

        # Initialise the font
        font = pygame.font.Font('../LEMONMILK-Medium.otf', 24)
        # Log in text
        text1 = font.render('Log In', True, self.BLACK)
        # Sign up text
        text2 = font.render('Sign Up', True, self.BLACK)
        # Draw the text unto the screen
        self.surface.blit(text1, (420, 133))
        self.surface.blit(text2, (590, 134))

    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password

    def check_password(self, hashed_password, password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

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

    def handle_sign_up(self, input_boxes, data_store):
        username = input_boxes[0].text
        password = input_boxes[1].text
        confirm_password = input_boxes[2].text

        if password != confirm_password:
            print("Passwords do not match!")
            return

        if len(username) < 4 or len(password) < 8:
            print("Username or password too short!")
            return

        hashed_password = self.hash_password(password)

        try:
            self.runsql('INSERT INTO tblPlayer (username, password) VALUES (?, ?)', (username, hashed_password))
            print("User created successfully!")
            data_store.add_data("username", username)
            data_store.add_data("password", password)
            player_id = ('''
            SELECT playerId
            FROM tblPlayer
            WHERE username = ?
            ''')
            values = (username,)
            id_result = self.runsql(player_id, values)
            id_1 = id_result[0]
            id = id_1[0]
            print(id)
            self.data_store.add_data("id", id)
            query = '''
            INSERT INTO tblPlayerStats (playerId, totalTrophies, pvpWins, pvpLosses, pveWins, pveLosses, arena)
            VALUES (?, 0, 0, 0, 0, 0, 1)
            '''
            values = (id,)
            self.runsql(query, values)
            loading("../")
            return 'logged in'
        except sqlite3.IntegrityError:
            print("Username already exists!")

    def handle_log_in(self, input_boxes, data_store):
        username = input_boxes[0].text
        password = input_boxes[1].text

        result = self.runsql('SELECT password FROM tblPlayer WHERE username = ?', (username,))
        if result:
            stored_password = result[0][0]
            if self.check_password(stored_password, password):
                print("Login successful!")
                data_store.add_data("username", username)
                data_store.add_data("password", password)
                player_id = ('''
                SELECT playerId
                FROM tblPlayer
                WHERE username = ?
                ''')
                values = (username,)
                id_result = self.runsql(player_id, values)
                id_1 = id_result[0]
                id = id_1[0]
                paddle_result = self.runsql('''
                    SELECT userPaddle
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id,))
                if paddle_result:
                    print("Paddle result:", paddle_result[0][0])
                else:
                    print("No paddle information found for the playerId")  # Debug statement

                get_trophies = self.runsql('''
                SELECT totalTrophies
                FROM tblPlayerStats
                WHERE playerId = ?
                ''', (id, ))

                get_arena = self.runsql('''
                    SELECT arena
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id, ))

                arena = get_arena[0][0]

                trophies = get_trophies[0][0]

                # this will check and update the player's arena everytime they log in
                if trophies <= 100:
                        self.runsql('''
                            UPDATE tblPlayerStats
                            SET arena = 1
                            WHERE playerId = ?
                        ''', (id,))

                if 100 <= trophies <= 350:
                        self.runsql('''
                            UPDATE tblPlayerStats
                            SET arena = 2
                            WHERE playerId = ?
                        ''', (id,))

                if 350 <= trophies <= 600:
                    if arena == 2:
                        self.runsql('''
                            UPDATE tblPlayerStats
                            SET arena = 3
                            WHERE playerId = ?
                        ''', (id,))

                if trophies < 0:
                    self.runsql('''
                    UPDATE tblPlayerStats
                    SET totalTrophies = 0
                    WHERE playerId = ?
                    ''', (id,))
                    print('set trophies to 0')

                get_pvp_wins = self.runsql('''
                    SELECT pvpWins
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id,))

                pvp_wins = get_pvp_wins[0][0]

                get_pvp_losses = self.runsql('''
                    SELECT pvpLosses
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id,))

                pvp_losses = get_pvp_losses[0][0]

                get_pve_wins = self.runsql('''
                    SELECT pveWins
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id,))

                pve_wins = get_pve_wins[0][0]

                get_pve_losses = self.runsql('''
                    SELECT pveLosses
                    FROM tblPlayerStats
                    WHERE playerId = ?
                ''', (id,))

                pve_losses = get_pve_losses[0][0]


                # print(trophies)
                print(username)
                print(id)
                print(f'your arena: {arena}')
                self.data_store.add_data('arena', arena)
                self.data_store.add_data('username', username)
                self.data_store.add_data("id", id)
                self.data_store.add_data("paddle", paddle_result[0][0])
                self.data_store.add_data("trophies", trophies)
                self.data_store.add_data('pvp_wins', pvp_wins)
                self.data_store.add_data('pvp_losses', pvp_losses)
                self.data_store.add_data('pve_wins', pve_wins)
                self.data_store.add_data('pve_losses', pve_losses)
                # t = self.data_store.get_data("trophies")
                # print(t)

                print()
                loading("../")
                return 'logged in'
            else:
                print("Incorrect password!")
        else:
            print("Username not found!")
    def sign_up(self, input_boxes):
        # Initialise the font
        font = pygame.font.Font('../LEMONMILK-Light.otf', 12)
        # Create a username text
        username_text = font.render('Please create a username. (Minimum 6 characters)', True, self.BLACK)
        self.surface.blit(username_text, (380, 250))
        # Create a password text
        password_text_1 = font.render('Please create a password.', True, self.BLACK)
        password_text_2 = font.render('Minimum 8 characters, including numbers', True, self.BLACK)
        confirm_password_text = font.render('Please confirm your password.', True, self.BLACK)
        # Draw the text unto the screen
        self.surface.blit(password_text_1, (380, 375))
        self.surface.blit(password_text_2, (380, 390))
        self.surface.blit(confirm_password_text, (380, 480))

        # Draw input boxes
        for box in input_boxes:
            box.draw(self.surface)

        # Draw submit button
        pygame.draw.rect(self.surface, self.MINT_GREEN, (480, 550, 150, 50), border_radius=10)
        submit_text = font.render('Submit', True, self.BLACK)
        self.surface.blit(submit_text, (520, 560))

    def log_in(self, input_boxes):
        font = pygame.font.Font('../LEMONMILK-Light.otf', 12)
        # Enter username text
        username_text = font.render('Please enter your username.', True, self.BLACK)
        self.surface.blit(username_text, (380, 250))
        # Enter password text
        password_text = font.render('Please enter your password.', True, self.BLACK)
        self.surface.blit(password_text, (380, 375))

        # Draw input boxes
        for box in input_boxes:
            box.draw(self.surface)

        # Draw submit button
        pygame.draw.rect(self.surface, self.MINT_GREEN, (480, 500, 150, 50), border_radius=10)
        submit_text = font.render('Submit', True, self.BLACK)
        self.surface.blit(submit_text, (520, 510))

    def show_screen(self):
        run = True
        display_sign_up = False
        display_log_in = False
        log_in_color = self.CERULEAN
        sign_up_color = self.CERULEAN
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if 390 <= mouse_pos[0] <= 540 and 125 <= mouse_pos[1] <= 175:
                        log_in_color = self.MINT_GREEN
                        sign_up_color = self.CERULEAN
                        display_sign_up = False
                        display_log_in = True
                    elif 565 <= mouse_pos[0] <= 715 and 125 <= mouse_pos[1] <= 175:
                        sign_up_color = self.MINT_GREEN
                        log_in_color = self.CERULEAN
                        display_sign_up = True
                        display_log_in = False

                    # Check for submit button click
                    if display_sign_up and 480 <= mouse_pos[0] <= 630 and 550 <= mouse_pos[1] <= 600:
                        if self.handle_sign_up(self.input_boxes_sign_up, self.data_store) == 'logged in':
                            return 'logged in'
                    elif display_log_in and 480 <= mouse_pos[0] <= 630 and 500 <= mouse_pos[1] <= 550:
                        if self.handle_log_in(self.input_boxes_log_in, self.data_store) == 'logged in':
                            return 'logged in'

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if display_sign_up:
                            if self.handle_sign_up(self.input_boxes_sign_up, self.data_store) == 'logged in':
                                return 'logged in'
                        elif display_log_in:
                            if self.handle_log_in(self.input_boxes_log_in, self.data_store) == 'logged in':
                                return 'logged in'

                # Handle input box events
                if display_sign_up:
                    for box in self.input_boxes_sign_up:
                        box.handle_event(event)
                if display_log_in:
                    for box in self.input_boxes_log_in:
                        box.handle_event(event)

            self.surface.fill(self.WHITE)  # make the surface clear
            self.draw(self.surface)
            self.draw_buttons(log_in_color, sign_up_color)
            if display_sign_up:
                self.sign_up(self.input_boxes_sign_up)
            if display_log_in:
                self.log_in(self.input_boxes_log_in)
            pygame.display.update()

