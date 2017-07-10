import unittest
from testDefinitions import *
from socket import *


class SinglePlayerTestCase(unittest.TestCase):
    def setUp(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))

    def tearDown(self):
        self.client_socket.close()

    def testInitialization(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_1 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(), 'Type "play" to be put in the matchmaking queue, "ranking" '
                                             'to see your ranking or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')
        self.client_socket.close()

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('login User_1 mypassword\r\n')
        self.assertEqual(self.receive(), 'log_ok')
        self.client_socket.send('ready\r\n')

    def testInitialization_DuplicateUsername(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_1 anotherpassword\r\n')
        self.assertEqual(self.receive(), 'reg_user_error')

    def testInitialization_IncorrectRegister_1(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_2\r\n')
        self.assertEqual(self.receive(), 'reg_command_error')

    def testInitialization_IncorrectRegister_2(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_2 mypassword something\r\n')
        self.assertEqual(self.receive(), 'reg_command_error')

    def testInitialization_ProhibitedChars(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_9 mypa\r\nssword\r\n')
        self.assertEqual(self.receive(), 'prohibited_chars')

    def testInitialization_DuplicateLogin(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_10 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')
        self.client_socket.close()

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('login User_10 mypassword\r\n')
        self.assertEqual(self.receive(), 'log_ok')
        self.client_socket.send('ready\r\n')

        client2_socket = socket(AF_INET, SOCK_STREAM)
        client2_socket.connect((serverName, serverPort))
        message = ''
        while 1:
            message += client2_socket.recv(messageSize)
            if message.endswith('\r\n'):
                message = message.split('\r\n')
                break
        self.assertEqual(message[0],
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        client2_socket.send('login User_10 mypassword\r\n')
        message = ''
        while 1:
            message += client2_socket.recv(messageSize)
            if message.endswith('\r\n'):
                message = message.split('\r\n')
                break
        self.assertEqual(message[0], 'already_logged_in')

    def testInitialization_IncorrectLogin_1(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_3 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')
        self.client_socket.close()

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('login User_3 mypassword something\r\n')
        self.assertEqual(self.receive(), 'login_command_error')

    def testInitialization_IncorrectLogin_2(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_4 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')
        self.client_socket.close()

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('login User_4 mypassword something\r\n')
        self.assertEqual(self.receive(), 'login_command_error')
        
    def testInitialization_IncorrectLogin_3(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_5 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')
        self.client_socket.close()

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((serverName, serverPort))
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('login User_5 wrongpassword\r\n')
        self.assertEqual(self.receive(), 'login_error')
        
    def testInitialization_InvalidCommand(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('something\r\n')
        self.assertEqual(self.receive(), 'unknown_command')
        self.client_socket.send('ready\r\n')

    def testMainLobby_Ranking(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_6 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('ranking\r\n')
        self.assertIsNot(self.receive(), '')
        self.client_socket.send('ranking_ok\r\n')

    def testMainLobby_Disconnect(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_7 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('quit\r\n')
        self.assertEqual(self.receive(), 'disconnect_ok')

    def testMainLobby_InvalidCommand(self):
        self.assertEqual(self.receive(),
                         'Please register using "register [username] [password]" or login to your account using '
                         '"login [username] [password]"')
        self.client_socket.send('register User_8 mypassword\r\n')
        self.assertEqual(self.receive(), 'reg_ok')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking '
                         'or "quit" to logout.')
        self.client_socket.send('something\r\n')
        self.assertEqual(self.receive(), 'unknown_command')
        self.client_socket.send('main_lobby\r\n')
        self.assertEqual(self.receive(),
                         'Type "play" to be put in the matchmaking queue, "ranking" to see your ranking'
                         ' or "quit" to logout.')

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
