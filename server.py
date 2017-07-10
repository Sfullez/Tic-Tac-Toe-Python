import threading
from socket import *
from time import *

__author__ = 'Federico Tammaro'
__email__ = 'federico.tammaro@stud.unifi.it'


class Server:

    def __init__(self):
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverPort = 13005
        self.messageSize = 1024
        self.usersDB = {}
        # 'Username': {'Password': 'password', 'isOnline': 1/0, 'Games': '#games', 'Won': '#won', 'Draw': '#draw',
        # 'Lost': '#lost'}
        self.games_played = 0
        self.player_queue = []
        self.games_lock = threading.Lock()  # Used to handle the played games counter
        self.queue_lock = threading.Lock()  # Used to handle the player queue by matchmaking thread
        self.ranking_lock = threading.Lock()  # Used to handle the player ranking,
        # which is updated by every single game thread
        try:
            self.serverSocket.bind(('', self.serverPort))
            self.serverSocket.listen(1)
        except:
            print "There was an error with the selected port (" + str(self.serverPort) + ")." \
                                                                                         " Change it in the .py file"
            exit(-1)

    def start(self):
        print "Server is now starting"
        threading.Thread(target=self.matchmaking_thread).start()
        self.server_loop()

    def server_loop(self):  # Insertion point for every connected client
        while 1:
            connection_socket, client_ip = self.serverSocket.accept()
            player = Player(connection_socket, client_ip)
            print 'Incoming connection from ' + str(client_ip)
            threading.Thread(target=self.client_connection_thread, args=(player,)).start()  # Gives control of the
            # player to a new thread

    def client_connection_thread(self, player):  # Thread which manages a client. N clients, N threads.
        try:
            player.send('Please register using "register [username] [password]" or login to your account using '
                        '"login [username] [password]"')
        except:
            print 'Error while waiting for ' + str(player.get_ip()) + ' response. Shutting connection down.'
            player.close_connection()
            exit(-1)

        try:
            while player.isActive:
                user_input = player.recv(self.messageSize, True).split()
                if not user_input:
                    player.send('prohibited_chars')
                if user_input[0] == 'register':
                    if self.client_register(user_input, player):
                        break
                elif user_input[0] == 'login':
                        if self.client_login(user_input, player):
                            break
                else:  # Any other not recognized command the client can send
                    player.send('unknown_command')
                    self.await_confirmation(player, 'ready')

            try:
                while player.isActive:
                    player.send('Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                                'or "quit" to logout.')
                    user_input = player.recv(self.messageSize, False)

                    if user_input == 'play':
                        with self.queue_lock:
                            self.player_queue.append(player)  # Appends a new user to the list of ready-to-play users
                        while True:  # Puts the player on hold while waiting for another player to enter matchmaking
                            if player.isPlaying:
                                break
                        player.send('opponent_found')
                        self.await_confirmation(player, 'ready')
                    elif user_input == 'ranking':
                        self.print_ranking(player)
                    elif user_input == 'quit':
                        player.send('disconnect_ok')
                        self.usersDB[player.username]['isOnline'] = 0
                        player.close_connection()
                        print 'Player ' + player.username + str(player.get_ip()) + ' logged out.'
                        break
                    else:
                        player.send('unknown_command')
                        self.await_confirmation(player, 'main_lobby')

                    while player.isPlaying:
                        sleep(0.5)
            except:
                self.usersDB[player.username]['isOnline'] = 0
        except:
            print 'Error while waiting for ' + str(player.get_ip()) + ' response. Shutting connection down.'
            player.close_connection()
            exit(-1)

    def client_register(self, user_input, player):
        if len(user_input) != 3:  # The user send an invalid register command, with an unexpected amount of arguments
            player.send('reg_command_error')
            print "Bad registration attempt. " + str(len(user_input)) + " arguments given."
            return False
        elif user_input[1] in self.usersDB:
            player.send('reg_user_error')  # Server signals a registration problem to the client, which now must
            # try the client initialization again
            print "New user tried to register with an already taken username."
            return False
        else:
            self.usersDB[user_input[1]] = {'Password': user_input[2], 'isOnline': 1, 'Games': 0, 'Won': 0,
                                           'Draw': 0, 'Lost': 0}
            player.send('reg_ok')  # Server signals a successful registration to the client
            self.await_confirmation(player, 'main_lobby')
            print "New user " + user_input[1] + " registered."
            player.username = user_input[1]
            return True

    def client_login(self, user_input, player):
        if len(user_input) != 3:  # The user send an invalid login command, with an unexpected amount of arguments
            player.send('login_command_error')
            print "Bad login attempt. " + str(len(user_input)) + " arguments given."
            return False
        elif user_input[1] in self.usersDB:
            if user_input[2] == self.usersDB[user_input[1]]['Password']:
                if self.usersDB[user_input[1]]['isOnline']:  # Correct username/password, but already online
                    player.send('already_logged_in')
                    print "User " + user_input[1] + " tried to log in while active in another session."
                    return False
                else:
                    self.usersDB[user_input[1]]['isOnline'] = 1
                    player.username = user_input[1]
                    player.send('log_ok')  # Server signals a successful login to the client
                    self.await_confirmation(player, 'main_lobby')
                    print "User " + user_input[1] + " logged in."
                    return True
        player.send('login_error')  # Server signals a login problem to the client,
        # which now must try the client initialization again
        print "Bad login attempt"
        return False

    def matchmaking_thread(self):
        print 'Matchmaking thread now starting.'
        while 1:
            if len(self.player_queue) >= 2:
                sleep(0.5)
                players = []
                with self.queue_lock:
                    for index in range(0, 2):
                        self.player_queue[0].isPlaying = True
                        players.append(self.player_queue.pop(0))
                threading.Thread(target=self.game_thread, args=(players[0], players[1])).start()
            sleep(0.5)

    def game_thread(self, player1, player2):  # N games, N threads, 2N playing users
        with self.games_lock:
            self.games_played += 1  # Increments game counter to give an unique ID to the game
            game_id = self.games_played
        print 'Starting game #' + str(game_id)

        player1.game_symbol = 'X'
        player2.game_symbol = 'O'
        game_board = ['1', '2', '3', '4', '5', '6', '7', '8', '9']  # Initially filled with numeric positions
        board_lock = threading.Lock()  # Lock used to prevent concurrency errors in the game thread

        if player1.isActive and player2.isActive:  # If both players are still active before game commences...
            try:
                player1.send('start_match')
                self.await_confirmation(player1, 'start')
                player2.send('start_match')
                self.await_confirmation(player2, 'start')
            except:  # If someone disconnects here, it will be caught on game_phase
                pass
            while True:  # Main game cycle, which alternates phases between the two players and stops in case
                # of a winning move
                if self.game_phase(player1, player2, game_board, board_lock):
                    break
                if self.game_phase(player2, player1, game_board, board_lock):
                    break
            print 'Game #' + str(game_id) + ' has now ended.'

            # Now the updated ranking will be send only if a player is still active
            try:
                player1.send(self.print_personal_ranking(player1))
                self.await_confirmation(player1, 'main_lobby')
            except:
                self.usersDB[player1.username]['isOnline'] = 0
                player1.isActive = False

            try:
                player2.send(self.print_personal_ranking(player2))
                self.await_confirmation(player2, 'main_lobby')
            except:
                self.usersDB[player2.username]['isOnline'] = 0
                player2.isActive = False

            player1.isPlaying = False
            player2.isPlaying = False
        else:  # Handles the disconnection of a player before the match start
            if player1.isActive:
                player1.send('match_fail')
                player1.isPlaying = False
            if player2.isActive:
                player2.send('match_fail')
                player2.isPlaying = False

    def game_phase(self, active, waiting, game_board, board_lock):
        try:  # If player is still active...
            active.send('your_turn')
            self.await_confirmation(active, 'ready')
        except:  # ...otherwise the other player wins the match
            try:
                self.usersDB[active.username]['isOnline'] = 0
                waiting.send('end_game')
                self.await_confirmation(waiting, 'end_game')
                waiting.send('Your opponent left the match.\nYou won!')
                self.await_confirmation(waiting, 'main_lobby')
            except:  # If he disconnected too, we won't send him anything
                pass
            print waiting.username + ' just won a match!'
            self.update_ranking(waiting, active, False)
            return True
        # If the waiting player disconnected, we will handle his disconnection on the next turn, when he will
        # be considered the active player of the phase
        valid_move = False
        game_over = False
        draw = False
        while not valid_move:
            game_over, draw, valid_move = self.player_move(active, game_board, board_lock, active.game_symbol)
        if active.isActive:  # If the active player was still active during his move...
            self.await_confirmation(active, 'end_turn')
            if game_over:  # If the active player has made a winning or final move during his active phase...
                active.send('end_game')
                self.await_confirmation(active, 'end_game')
                waiting.send('end_game')
                self.await_confirmation(waiting, 'end_game')
                if draw:  # If the board has filled up but no one won...
                    try:
                        active.send(self.print_board(game_board) + "It's a draw, folks!")
                        self.await_confirmation(active, 'get_ranking')
                    except:
                        pass

                    try:
                        waiting.send(self.print_board(game_board) + "It's a draw, folks!")
                        self.await_confirmation(waiting, 'get_ranking')
                    except:
                        pass

                    self.update_ranking(active, waiting, True)
                    return True
                else:
                    print active.username + ' just won a match!'
                    try:
                        active.send(self.print_board(game_board) + 'You won!')
                        self.await_confirmation(active, 'get_ranking')
                    except:
                        pass

                    try:
                        waiting.send(self.print_board(game_board) + 'You lost!')
                        self.await_confirmation(waiting, 'get_ranking')
                    except:
                        pass

                    self.update_ranking(active, waiting, False)
                    return True
        else:  # If the active player disconnected during his move phase...
            try:
                self.usersDB[active.username]['isOnline'] = 0
                waiting.send('end_game')
                self.await_confirmation(waiting, 'end_game')
                waiting.send('Your opponent left the match.\n You won!')
                self.await_confirmation(waiting, 'main_lobby')
            except:
                pass
            print waiting.username + ' just won a match!'
            self.update_ranking(waiting, active, False)
            return True

    def player_move(self, player, game_board, board_lock, symbol):
        try:
            message = "It's your turn, you are '" + symbol + "'. Please send the number of the corresponding box.\n"
            player.send(message + self.print_board(game_board))
            player_input = player.recv(self.messageSize, False)  # Receives input from the player, where to place
            # his symbol
            print 'Received player input'
            if self.valid_move(player_input, game_board, board_lock, symbol):  # Checks if the player has made
                # a valid move....
                player.send('valid_move')
                self.await_confirmation(player, 'get_board')
                player.send(self.print_board(game_board))
                return self.check_board(game_board)
            else:  # ...otherwise it won't exit the loop in game_phase
                player.send('invalid_move')
                self.await_confirmation(player, 'ready')
                return False, False, False
        except:  # Propagates the disconnection notice to game_phase instead of handling it...
            print 'Error while waiting for ' + str(player.get_ip()) + ' response.'
            self.usersDB[player.username]['isOnline'] = 0
            player.isActive = False  # ...using the player isActive status
            player.close_connection()
            return True, False, True

    def print_board(self, game_board):
        return ('{}|{}|{}\n' * 3).format(*game_board)  # Formatting method to print the board without using a loop
        # without iterating (explicitly) in the game board

    def check_board(self, game_board):  # Checks if a winning move has been made or if the board is filled up...
        if((game_board[0] == game_board[1] and game_board[1] == game_board[2])
           or (game_board[0] == game_board[3] and game_board[3] == game_board[6])
           or (game_board[1] == game_board[4] and game_board[4] == game_board[7])
           or (game_board[3] == game_board[4] and game_board[4] == game_board[5])
           or (game_board[6] == game_board[7] and game_board[7] == game_board[8])
           or (game_board[2] == game_board[5] and game_board[5] == game_board[8])
           or (game_board[0] == game_board[4] and game_board[4] == game_board[8])
           or (game_board[2] == game_board[4] and game_board[4] == game_board[6])):
            return True, False, True
        if any(str(x) in game_board for x in range(1, 10)):  # ...checking if there's a position number left in the grid
            return False, False, True
        return True, True, True

    def valid_move(self, player_input, game_board, board_lock, symbol):
        if player_input in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:  # Not using range(1, 10) to avoid converting
            # player_input from string to int
            if player_input in game_board:
                with board_lock:
                    game_board[int(player_input) - 1] = symbol
                return True
        return False

    def update_ranking(self, winner, loser, draw):
        if draw:
            with self.ranking_lock:
                self.usersDB[winner.username]['Games'] += 1
                self.usersDB[winner.username]['Draw'] += 1
                self.usersDB[loser.username]['Games'] += 1
                self.usersDB[loser.username]['Draw'] += 1
        else:
            with self.ranking_lock:
                self.usersDB[winner.username]['Games'] += 1
                self.usersDB[winner.username]['Won'] += 1
                self.usersDB[loser.username]['Games'] += 1
                self.usersDB[loser.username]['Lost'] += 1

    def print_personal_ranking(self, user):
        ranking = ''
        ranking += 'Games played: ' + str(self.usersDB[user.username]['Games'])
        ranking += ' | Won: ' + str(self.usersDB[user.username]['Won'])
        ranking += ' | Draw: ' + str(self.usersDB[user.username]['Draw'])
        ranking += ' | Lost: ' + str(self.usersDB[user.username]['Lost'])
        return ranking

    def print_ranking(self, player):
        sorted_dic = sorted(self.usersDB.items(), key=lambda x: x[1]['Won'], reverse=True)
        ranking_text = ''
        with self.ranking_lock:
            for index in range(0, len(sorted_dic)):
                ranking_text += sorted_dic[index][0]
                ranking_text += ' | Played games: ' + str(sorted_dic[index][1]['Games'])
                ranking_text += ' Won: ' + str(sorted_dic[index][1]['Won'])
                ranking_text += ' Draw: ' + str(sorted_dic[index][1]['Draw'])
                ranking_text += ' Lost: ' + str(sorted_dic[index][1]['Lost'])
                if index != len(sorted_dic) - 1:
                    ranking_text += '\n'
        player.send(ranking_text)
        self.await_confirmation(player, 'ranking_ok')

    def await_confirmation(self, player, message):
        while 1:
            if player.recv(self.messageSize, False) == message:
                break


class Player:

    """
        Utility class made for a more readable code. Used to simplify send and receive commands and to handle the
        player status.
    """

    def __init__(self, connection_socket, client_ip):
        self.__connectionSocket = connection_socket
        self.__ip = client_ip
        self.isActive = True
        self.isPlaying = False
        self.username = ''
        self.game_symbol = ''

    def send(self, string):
        self.__connectionSocket.send(string + '\r\n')

    def recv(self, msg_size, init):
        message = ''
        while 1:
            message += self.__connectionSocket.recv(msg_size)
            if message.endswith('\r\n'):
                message = message.split('\r\n')
                break
        if init:  # If we're in the initialization phase, we must check if there's \r\n in the username of password
            if len(message) > 2:
                return ''
        return message[0]

    def get_ip(self):
        return self.__ip

    def close_connection(self):
        self.__connectionSocket.close()


server = Server()
server.start()
