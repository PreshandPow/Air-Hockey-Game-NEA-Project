# server.py
import socket
import threading
import json

HEADER = 1024  # max amount of bytes that can be sent
PORT = 5055
SERVER = socket.gethostbyname(socket.gethostname())
print(SERVER)
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT!'
PLAYERS = []
LOBBY1 = {'queue1': [],
          'queue2': [],
          'queue3': []}

LOBBY2 = {'queue1': [],
          'queue2': [],
          'queue3': []}

LOBBY3 = {'queue1': [],
          'queue2': [],
          'queue3': []}

MAX_CONNECTIONS = 2
LOCK = threading.Lock()  # Lock for threads safety
game_is_active = False

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def broadcast(message, current_conn):
    with LOCK:
        for player in PLAYERS:
            if player != current_conn:
                try:
                    player.send(message.encode(FORMAT))
                except Exception as e:
                    print(f'Error while broadcasting: {e}')


def handle_client(conn, addr):
    with LOCK:
        print(f'[NEW CONNECTION] {addr} connected')
        PLAYERS.append(conn)
        if len(LOBBY1['queue1']) == 1:
            conn.send('you are player1'.encode(FORMAT))
        elif len(LOBBY1['queue1']) == 2:
            conn.send('you are player2'.encode(FORMAT))

    connected = True
    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)

                msg = conn.recv(msg_length).decode(FORMAT)

                if msg == DISCONNECT_MESSAGE:
                    print('DISCONNECT MESSAGE RECEIVED')
                    connected = False
                    with LOCK:
                        PLAYERS.remove(conn)
                        print(f'[DISCONNECTED] {addr} disconnected')

                else:
                    try:
                        PUCK_POSITION = {'x': 0, 'y': 0}
                        position_data = json.loads(msg)
                        if 'x' in position_data and 'y' in position_data:
                            # Paddle position, broadcast as-is
                            broadcast(msg, conn)

                        elif 'id' in position_data and 'puck_x' in position_data and 'puck_y' in position_data:
                            # Update and broadcast puck position
                            print(position_data['id'])
                            with LOCK:
                                PUCK_POSITION['x'] = position_data['puck_x']
                                PUCK_POSITION['y'] = position_data['puck_y']
                            broadcast(json.dumps({'puck_x': PUCK_POSITION['x'], 'puck_y': PUCK_POSITION['y']}), conn)
                            # print(f"Updated puck position: {PUCK_POSITION}")  # debug log

                        elif 'id' in position_data and 'trophies' in position_data:
                            p_id = position_data['id']
                            trophies = position_data['trophies']
                            # print(p_id, trophies)

                            if trophies <= 100:
                                assigned = True
                                for queue in LOBBY1:
                                    QUEUE = LOBBY1[queue]

                                    if len(QUEUE) < 2:
                                        QUEUE.append(conn)
                                        assigned = True
                                        print(f'player id: {p_id} has been added to lobby 1 {queue}')
                                        send_start_signal()
                                        break

                                if not assigned:
                                    print('Match making is currently full. Please try again later.')

                            elif trophies <= 350:
                                assigned = True
                                for queue in LOBBY2:
                                    QUEUE = LOBBY2[queue]

                                    if len(QUEUE) < 2:
                                        QUEUE.append(conn)
                                        assigned = True
                                        print(f'player id: {p_id} has been added to lobby 2 {queue}')
                                        send_start_signal()
                                        break

                                if not assigned:
                                    print('Match making is currently full. Please try again later.')

                            elif trophies <= 600:
                                assigned = True
                                for queue in LOBBY3:
                                    QUEUE = LOBBY3[queue]

                                    if len(QUEUE) < 2:
                                        QUEUE.append(conn)
                                        assigned = True
                                        print(f'player id: {p_id} has been added to lobby 3 {queue}')
                                        send_start_signal()
                                        break

                                if not assigned:
                                    print('Match making is currently full. Please try again later.')

                            else:
                                print('Error while assigning player to queue. Please match make again.')
                                PLAYERS.remove(conn)

                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {msg}")
        except Exception as e:
            print(f'Error while handling message: {e}')
            PLAYERS.remove(conn)
            connected = False

    conn.close()


def send_start_signal():
    with LOCK:  # Lock for thread safety
        for queue in LOBBY1:
            if len(LOBBY1[queue]) >= 2:
                print(f'Starting round between Lobby 1 {queue} players')
                for conn in LOBBY1[queue]:
                    try:
                        # print('stage 3')
                        conn.send('startgame'.encode(FORMAT))
                        print(f"Sending START to {conn}")
                        LOBBY1[queue] = []
                    except Exception as e:
                        print(f'Error while sending start game: {e}')
            else:
                pass

        for queue in LOBBY2:
            if len(LOBBY2[queue]) >= 2:
                print(f'Starting round between Lobby 2 {queue} players')
                for conn in LOBBY2[queue]:
                    try:
                        # print('stage 3')
                        conn.send('startgame'.encode(FORMAT))
                        print(f"Sending START to {conn}")
                        LOBBY2[queue] = []
                    except Exception as e:
                        print(f'Error while sending start game: {e}')
            else:
                pass

        for queue in LOBBY3:
            if len(LOBBY3[queue]) >= 2:
                print(f'Starting round between Lobby 3{queue} players')
                for conn in LOBBY3[queue]:
                    try:
                        # print('stage 3')
                        conn.send('startgame'.encode(FORMAT))
                        print(f"Sending START to {conn}")
                        LOBBY3[queue] = []
                    except Exception as e:
                        print(f'Error while sending start game: {e}')
            else:
                pass


def start():
    server.listen()
    print(f'[LISTENING] Server is listening on {SERVER}')
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        send_start_signal()  # Check and send the start signal for new connections


print('[STARTING] Server is starting...')
if __name__ == '__main__':
    start()
