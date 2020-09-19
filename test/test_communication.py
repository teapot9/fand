"""fand.communication tests"""

import unittest.mock as mock

import pytest

com = pytest.importorskip('fand.communication')


@pytest.fixture(autouse=True)
def cleanup_sockets():
    """cleanup com.__SOCKETS__"""
    yield
    for sock in com.__SOCKETS__.copy():
        com.reset_connection(sock)


@pytest.fixture
def mock_socket():
    """create mock socket"""
    sock = mock.Mock()
    com.add_socket(sock)
    yield sock


class TestAddSocket:
    """add_socket tests"""

    def test_sanity(self):
        """sanity checks"""
        sock = mock.Mock()
        com.add_socket(sock)
        assert com.is_socket_open(sock)

    @mock.patch('fand.util.terminating')
    def test_terminating(self, mock_terminating):
        """check when terminating is true"""
        sock = mock.Mock()
        mock_terminating.return_value = True
        with pytest.raises(com.TerminatingError):
            com.add_socket(sock)
        assert not com.is_socket_open(sock)


class TestSend:
    """send() tests"""

    @mock.patch('pickle.dumps')
    def test_sanity(self, mock_dumps, mock_socket):
        """sanity checks"""
        data = b'10 bytes  '
        header = com.HEADER_MAGIC + b'000a'
        mock_dumps.return_value = data
        mock_socket.send.return_value = len(header + data)
        com.send(mock_socket, 'req', 'arg1', 'arg2', 'arg3')
        mock_dumps.assert_called_once_with(('req', ('arg1', 'arg2', 'arg3')))
        mock_socket.send.assert_called_once_with(header + data)


class TestRecv:
    """recv() tests"""

    @mock.patch('pickle.loads')
    def test_sanity(self, mock_loads, mock_socket):
        """sanity checks"""
        data = b'10 bytes  '
        header = com.HEADER_MAGIC + b'000a'
        mock_socket.recv.side_effect = [header, data]
        mock_loads.return_value = ('req', ('arg1', 'arg2', 'arg3'))
        assert com.recv(mock_socket) == ('req', ('arg1', 'arg2', 'arg3'))
        mock_loads.assert_called_once_with(data)
        mock_socket.recv.assert_called()


class TestConnect:
    """connect() tests"""

    @mock.patch('socket.socket')
    def test_sanity(self, mock_socket_object, mock_socket):
        """sanity checks"""
        mock_socket_object.return_value = mock_socket
        assert com.connect('addr', 1234) == mock_socket
        mock_socket.connect.assert_called_once_with(('addr', 1234))
        assert com.is_socket_open(mock_socket)


class TestResetConnection:
    """reset_connection() tests"""

    def test_sanity(self, mock_socket):
        """sanity checks"""
        com.reset_connection(mock_socket, notice=False)
        mock_socket.shutdown.assert_called_once()
        mock_socket.close.assert_called_once()
        assert not com.is_socket_open(mock_socket)

    @mock.patch('fand.communication.send')
    def test_notice(self, mock_send, mock_socket):
        """reset connection with notice"""
        com.reset_connection(mock_socket, 'error message', notice=True)
        mock_send.assert_called_once_with(mock_socket, com.Request.DISCONNECT,
                                          'error message')
        mock_socket.shutdown.assert_called()
        mock_socket.close.assert_called()
        assert not com.is_socket_open(mock_socket)
