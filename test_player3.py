import unittest
from testDefinitions import *
from socket import *


class Player3TestCase(unittest.TestCase):
    def setUp(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        
    def tearDown(self):
        self.client_socket.close()

    def testGame(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_13 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('play\r\n')
        self.assertEqual(self.receive(), 'opponent_found')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(), 'start_match')
        self.client_socket.send('start\r\n')
        self.assertEqual(self.receive(), 'your_turn')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(),
                         "It's your turn, you are 'X'. Please send the number of the corresponding box.\n1|2|3\n4|5|6\n7|8|9\n")
        self.client_socket.send('1\r\n')
        self.assertEqual(self.receive(), 'valid_move')
        self.client_socket.send('get_board\r\n')
        self.assertEqual(self.receive(), 'X|2|3\n4|5|6\n7|8|9\n')
        self.client_socket.send('end_turn\r\n')
        self.assertEqual(self.receive(), 'your_turn')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(),
                         "It's your turn, you are 'X'. Please send the number of the corresponding box.\nX|O|3\n4|5|6\n7|8|9\n")
        self.client_socket.send('4\r\n')
        self.assertEqual(self.receive(), 'valid_move')
        self.client_socket.send('get_board\r\n')
        self.assertEqual(self.receive(), 'X|O|3\nX|5|6\n7|8|9\n')
        self.client_socket.send('end_turn\r\n')
        self.assertEqual(self.receive(), 'your_turn')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(),
                         "It's your turn, you are 'X'. Please send the number of the corresponding box.\nX|O|3\nX|O|6\n7|8|9\n")
        self.client_socket.send('8\r\n')
        self.assertEqual(self.receive(), 'valid_move')
        self.client_socket.send('get_board\r\n')
        self.assertEqual(self.receive(), 'X|O|3\nX|O|6\n7|X|9\n')
        self.client_socket.send('end_turn\r\n')
        self.assertEqual(self.receive(), 'your_turn')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(),
                         "It's your turn, you are 'X'. Please send the number of the corresponding box.\nX|O|3\nX|O|6\nO|X|9\n")
        self.client_socket.send('3\r\n')
        self.assertEqual(self.receive(), 'valid_move')
        self.client_socket.send('get_board\r\n')
        self.assertEqual(self.receive(), 'X|O|X\nX|O|6\nO|X|9\n')
        self.client_socket.send('end_turn\r\n')
        self.assertEqual(self.receive(), 'your_turn')
        self.client_socket.send('ready\r\n')
        self.assertEqual(self.receive(),
                         "It's your turn, you are 'X'. Please send the number of the corresponding box.\nX|O|X\nX|O|O\nO|X|9\n")
        self.client_socket.send('9\r\n')
        self.assertEqual(self.receive(), 'valid_move')
        self.client_socket.send('get_board\r\n')
        self.assertEqual(self.receive(), 'X|O|X\nX|O|O\nO|X|X\n')
        self.client_socket.send('end_turn\r\n')
        self.assertEqual(self.receive(), 'end_game')
        self.client_socket.send('end_game\r\n')
        self.assertEqual(self.receive(), "X|O|X\nX|O|O\nO|X|X\nIt's a draw, folks!")
        self.client_socket.send('get_ranking\r\n')
        self.assertEqual(self.receive(), 'Games played: 1 | Won: 0 | Draw: 1 | Lost: 0')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(), 'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking or "quit" to logout.')

    def receive(self):
        message = ''
        while 1:
            message += self.client_socket.recv(messageSize)
            if message.endswith('\r\n'):
                message = message.split('\r\n')
                break
        return message[0]


if __name__ == "__main__":
    unittest.main()