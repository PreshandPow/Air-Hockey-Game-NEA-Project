import pygame
from menu import Menu
from sign_in import signIn
from play_pve import Pve
from waiting_screen import WaitingScreen
from Inventory import Inventory
from v2.stats_page import Stats


# Initialize pygame
pygame.display.init()
pygame.font.init()

# Set up the display surface
surface_width, surface_height = 1100, 650
surface = pygame.display.set_mode((surface_width, surface_height))
pygame.display.set_caption('Air Hockey!')

# Create sign-in instance and show the screen
sign_in_instance = signIn(surface)

login_status = sign_in_instance.show_screen()

# Check if user logged in successfully
if login_status == 'logged in':
    session_info = sign_in_instance.get_session_data()
    loop_menu = True
    while loop_menu:
        menu_instance = Menu(surface, session_info, '../background_gif.gif')
        next_screen = menu_instance.show_screen()

        # handle calling the pve screen
        if next_screen == 'pve':
            pve_instance = Pve(surface, session_info)
            pve_instance.show_screen()

        # handle calling the inventory screen
        elif next_screen == 'inv':
            inv = Inventory(surface, None, session_info)
            res = inv.show_screen()
            print('opened inventory')
            if res == 'back':
                continue

        # handle calling the statistics page
        elif next_screen == 'stat':
            stat = Stats(surface, None, session_info)
            res = stat.show_screen()
            print('opened stats page')
            if res == 'back':
                continue

        # handle calling the pvp page
        elif next_screen == 'pvp':
            waiting_screen = WaitingScreen(session_info)
            run = waiting_screen.run()
            print('game abt to end')
            if run == 'game ended':
                print('returned end')
                continue


        elif next_screen in ['gobacktomenu', 'returned']:
            continue

        elif next_screen == 'exit':
            loop_menu = False

pygame.quit()
