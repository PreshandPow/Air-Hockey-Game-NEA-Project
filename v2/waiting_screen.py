import json
import pygame
from pygame.locals import *
import threading
from PIL import Image
import socket
from play_pvp import Pvp

# Configuration for client connection
HEADER = 1024
PORT = 5055
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT!'
HOME = '192.168.124.1'
COLLEGE = '10.90.78.70'
SERVER = '192.168.167.162'
ADDR = (SERVER, PORT)

class WaitingScreen:
    def __init__(self, sessionInfo, width=1100, height=650):
        pygame.init()

        # Display and session settings
        self.width = width
        self.height = height
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Waiting Screen")
        self.session_info = sessionInfo
        self.frame_index = 0
        self.running = True
        self.match_found = False
        self.player = None
        self.opponent = None
        self.data_store = sessionInfo
        self.disconnect = False

        # Colors
        self.RICH_BLACK = (14, 19, 23)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)

        # Load GIF frames
        self.gif_frames = self.load_and_transform_gif("../loading_screen3.gif", 0, (1100, 650))

        # Set up the client socket but don’t connect yet
        self.client = None

    # During initialization
    def connect_to_server(self):
        """Initialize and connect the client socket."""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            playerid = self.data_store.get_data('id')
            trophies = self.data_store.get_data('trophies')
            # print(playerid, trophies)

            player_info = {'id': playerid,
                           'trophies': trophies}

            self.client.connect(ADDR)
            print("Connected to server.")
            # print(player_info['id'], player_info['trophies'])

            self.send_message(json.dumps(player_info))

        except ConnectionRefusedError:
            print("Connection failed. Please check if the server is running and the address is correct.")
            self.running = False

    # Ensure this only happens once and before attempting any sends

    def load_and_transform_gif(self, gif_path, rotation_angle, new_size):
        gif = Image.open(gif_path)
        frames = []
        try:
            while True:
                frame = gif.convert('RGBA')
                pygame_image = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                rotated_frame = pygame.transform.rotate(pygame_image, rotation_angle)
                resized_frame = pygame.transform.scale(rotated_frame, new_size)
                frames.append(resized_frame)
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        return frames

    def update_frame(self):
        self.frame_index = (self.frame_index + 1) % len(self.gif_frames)

    def draw(self):
        self.window.fill(self.RICH_BLACK)
        self.window.blit(self.gif_frames[self.frame_index], (0, 0))
        font = pygame.font.Font('../LEMONMILK-Bold.otf', 50)
        text = font.render('SEARCHING FOR OPPONENT', True, self.WHITE)
        self.window.blit(text, (175, 50))
        self.draw_cancel_button()

    def draw_cancel_button(self):
        button_rect = pygame.Rect((900, 550), (150, 50))
        pygame.draw.rect(self.window, self.RED, button_rect)
        font = pygame.font.Font(None, 36)
        text = font.render("Cancel", True, self.WHITE)
        text_rect = text.get_rect(center=button_rect.center)
        self.window.blit(text, text_rect)
        return button_rect

    def check_cancel_button(self, mouse_pos):
        # Check if the Cancel button is clicked
        button_rect = pygame.Rect((900, 550), (150, 50))
        if button_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
            self.cancel_matchmaking()
        return None  # Continue in waiting screen if not clicked

    def cancel_matchmaking(self):
        """Cancel matchmaking by sending a disconnect message and closing the socket."""
        if self.client:
            self.send_message(DISCONNECT_MESSAGE)  # Safe check for sends
            print("Disconnect message sent.")
            self.client.close()  # Close the socket
            self.client = None  # Prevent further use
            self.running = False
            print("Client socket closed, matchmaking canceled.")
        return 'back_to_menu'

    def run_pvp_game(self, surface, player_pos, opponent_pos, client):
        # pygame.quit()  # Close the waiting screen window
        username = self.data_store.get_data('username')
        player_id = self.data_store.get_data("id")
        trophies = self.data_store.get_data('trophies')
        arena = self.data_store.get_data('arena')
        game = Pvp(surface, player_pos, opponent_pos, client, username, player_id, trophies, arena, self.disconnect)  # Create an instance of Pvp
        result = game.show_screen()  # Call show_screen on that instance
        return result

    def start_match(self, proper_surface, player_pos, opponent_pos):
        if self.match_found:
            print('Opponent found. Starting match in 3 seconds...')
            run = self.run_pvp_game(proper_surface, player_pos, opponent_pos, self.client)  # Start the PVP game
            return run

    def listen_for_server_messages(self):
        while self.running and self.client:
            try:
                msg = self.client.recv(HEADER).decode(FORMAT)

                if msg == 'startgame':
                    self.match_found = True

                elif msg == DISCONNECT_MESSAGE:
                    self.running = False
                    break

                elif msg == 'od':
                    print('1st check opponent disconnected')
                    self.disconnect = True

                elif msg == 'you are player1':
                    self.player = 1
                    self.opponent = 2
                    # print(self.player)

                elif msg == 'you are player2':
                    self.player = 2
                    #self.opponent = self.client.recv(HEADER).decode(FORMAT)
                    self.opponent = 1
                    # print(self.player)




            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False
                break

        if self.client:
            self.client.close()

    def send_message(self, msg):
        if self.client:
            message = msg.encode(FORMAT)
            send_length = f"{len(message):<{HEADER}}".encode(FORMAT)
            self.client.send(send_length)
            self.client.send(message)
            # self.client.send()

    def run(self):
        self.connect_to_server()
        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()

        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.cancel_matchmaking()

            mouse_pos = pygame.mouse.get_pos()

            if self.check_cancel_button(mouse_pos) == 'back_to_menu':
                return 'gobacktomenu'



            self.update_frame()
            self.draw()

            if self.match_found:
                player_pos = self.player
                opponent_pos = self.opponent
                start = self.start_match(self.window, player_pos, opponent_pos)  # Pass the actual Pygame surface
                if start == 'game ended':
                    print('game end')
                    return 'game ended'

            pygame.display.flip()
            clock.tick(60)