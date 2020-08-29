"""fand.fanctl tests"""

import datetime
import unittest.mock as mock

import pytest

com = pytest.importorskip('fand.communication')
fanctl = pytest.importorskip('fand.fanctl')


@pytest.fixture
def mock_datetime():
    class MockDatetime(datetime.datetime):
        """Mock the datetime.datetime class"""
        now = mock.Mock()
    real_datetime, datetime.datetime = datetime.datetime, MockDatetime
    yield MockDatetime
    datetime.datetime = real_datetime


@pytest.fixture
def server_socket():
    """create mock socket"""
    sock = mock.Mock()
    com.add_socket(sock)
    yield sock
    if com.is_socket_open(sock):
        com.reset_connection(sock)


class TestActionSendRaw:
    """_action_send_raw() tests"""

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_sanity(self, mock_recv, mock_send, server_socket):
        """sanity checks"""
        mock_recv.return_value = ('req', ('rarg1', 'rarg2', 'rarg3'))
        fanctl._action_send_raw(server_socket, com.Request.PING, 'arg1',
                                'arg2', 'arg3')
        mock_send.assert_called_once_with(server_socket, com.Request.PING,
                                          'arg1', 'arg2', 'arg3')
        mock_recv.assert_called_once_with(server_socket)


class TestActionSetPwmOverride:
    """_action_set_pwm_override() tests"""
    VALUES_TO_TEST = {'0': 0, '100': 100, '9': 9, '56': 56, 'none': None,
                      'None': None, 'nOnE': None, 0: 0, 100: 100, 9: 9, 56: 56}
    WRONG_VALUES = ['string', '-1-1']

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_sanity(self, mock_recv, mock_send, server_socket):
        """sanity checks"""
        mock_recv.return_value = (com.Request.ACK, ())
        shelf_id = 'shelf id'
        for value, result in type(self).VALUES_TO_TEST.items():
            fanctl._action_set_pwm_override(server_socket, shelf_id, value)
            mock_send.assert_called_with(
                server_socket, com.Request.SET_PWM_OVERRIDE, shelf_id, result
            )
            mock_recv.assert_called_with(server_socket)

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_invalid_number(self, mock_recv, mock_send, server_socket):
        """test for invalid numbers"""
        shelf_id = 'shelf id'
        for value in type(self).WRONG_VALUES:
            with pytest.raises(ValueError):
                fanctl._action_set_pwm_override(server_socket, shelf_id, value)
            mock_send.assert_not_called()
            mock_recv.assert_not_called()


class TestActionSetPwmExpireOn:
    """_action_set_pwm_expire_on() tests"""
    VALUES_TO_TEST = {
        '2000-04-30T21:30:59':
        datetime.datetime(2000, 4, 30, 21, 30, 59),
        '2050-12-31T00:40:21.55+02:00':
        datetime.datetime(2050, 12, 31,  0, 40, 21, 550000,
                          datetime.timezone(datetime.timedelta(hours=2))),
    }
    WRONG_VALUES = ['string', '-1-1']

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_sanity(self, mock_recv, mock_send, server_socket):
        """sanity checks"""
        mock_recv.return_value = (com.Request.ACK, ())
        shelf_id = 'shelf id'
        for value, result in type(self).VALUES_TO_TEST.items():
            fanctl._action_set_pwm_expire_on(server_socket, shelf_id, value)
            assert mock_send.call_args[0][3] == result
            mock_recv.assert_called_with(server_socket)

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_invalid_date(self, mock_recv, mock_send, server_socket):
        """test with invalid date strings"""
        shelf_id = 'shelf id'
        for value in type(self).WRONG_VALUES:
            with pytest.raises(ValueError):
                fanctl._action_set_pwm_expire_on(server_socket,
                                                 shelf_id, value)
            mock_send.assert_not_called()
            mock_recv.assert_not_called()


class TestActionSetPwmExpireIn:
    """_action_set_pwm_expire_in() tests"""
    VALUES_TO_TEST = {
        '4h2m1s': datetime.timedelta(0, 1, 0, 0, 2, 4),
        '8d13s': datetime.timedelta(8, 13),
        '40': datetime.timedelta(0, 40),
        '5:40': datetime.timedelta(0, 40, 0, 0, 5),
        '1:10:2': datetime.timedelta(0, 2, 0, 0, 10, 1),
        '1:00:10:00.123': datetime.timedelta(1, 0, 0, 123, 10, 0),
    }
    WRONG_VALUES = ['12l', 'string', '82h6d', '3d5h2d']

    def setup_method(self):
        """setup zero_delta"""
        self.zero_delta = datetime.timedelta()
        self.now = datetime.datetime.now()

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_sanity(self, mock_recv, mock_send, server_socket, mock_datetime):
        """sanity checks"""
        mock_recv.return_value = (com.Request.ACK, ())
        shelf_id = 'shelf id'
        for value, result in type(self).VALUES_TO_TEST.items():
            mock_datetime.now.return_value = self.now
            fanctl._action_set_pwm_expire_in(server_socket, shelf_id, value)
            assert mock_send.call_args[0][3] == self.now + result
            mock_recv.assert_called_with(server_socket)

    @mock.patch('fand.communication.send')
    @mock.patch('fand.communication.recv')
    def test_invalid_duration(self, mock_recv, mock_send, server_socket):
        """test with invalid duration strings"""
        shelf_id = 'shelf id'
        for value in type(self).WRONG_VALUES:
            with pytest.raises(ValueError):
                fanctl._action_set_pwm_expire_in(server_socket,
                                                 shelf_id, value)
            mock_send.assert_not_called()
            mock_recv.assert_not_called()
