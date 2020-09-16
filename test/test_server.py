"""fand.server tests"""

import datetime
import unittest.mock as mock

import pytest

server = pytest.importorskip('fand.server')
com = pytest.importorskip('fand.communication')


def is_cpu_temp_available():
    """Returns True if CPU temperature monitoring is available"""
    psutil = pytest.importorskip('psutil')
    return psutil.sensors_temperatures().get('coretemp') is not None


@pytest.fixture
def mock_socket():
    """create mock socket"""
    sock = mock.Mock()
    com.add_socket(sock)
    yield sock
    if com.is_socket_open(sock):
        com.reset_connection(sock)


@pytest.fixture
def mock_shelf():
    """create mock shelf, handle server.__SHELVES__ dict"""
    shelf = mock.Mock()
    shelf.identifier = 'mock_shelf'
    server.__SHELVES__[shelf.identifier] = shelf
    yield shelf
    server.__SHELVES__ = {}


@pytest.fixture
def mock_pysmart_devices():
    """create mock list of pysmart Device"""
    devices_list = []
    for serial in ['SERIAL1', 'SERIAL2', 'SERIAL3', 'SERIAL4', 'SERIAL5']:
        device = mock.Mock()
        device.serial = serial
        devices_list.append(device)
    return devices_list


class TestDevice:
    """Device tests"""

    def setup_method(self):
        """create Device object to use"""
        with mock.patch('fand.server.Device.find'):
            self.device = server.Device('SERIAL999', 'drive position')
            self.cpu = server.Device('cpu', 'the cpu')

    @mock.patch('pySMART.DeviceList')
    def test_find_hdd(self, mock_pysmart_device_list,
                      mock_pysmart_devices):
        """Device.find() sanity checks for HDD"""
        pysmart_device = mock.Mock()
        pysmart_device.serial = 'SERIAL999'
        pysmart_device.is_ssd = False
        mock_pysmart_devices.append(pysmart_device)
        mock_pysmart_device_list().devices = mock_pysmart_devices
        assert self.device.find().pysmart == pysmart_device
        assert self.device.find().type == server.Device.DeviceType.HDD

    @mock.patch('pySMART.DeviceList')
    def test_find_ssd(self, mock_pysmart_device_list,
                      mock_pysmart_devices):
        """Device.find() sanity checks for SSD"""
        pysmart_device = mock.Mock()
        pysmart_device.serial = 'SERIAL999'
        pysmart_device.is_ssd = True
        mock_pysmart_devices.append(pysmart_device)
        mock_pysmart_device_list().devices = mock_pysmart_devices
        assert self.device.find().pysmart == pysmart_device
        assert self.device.find().type == server.Device.DeviceType.SSD

    def test_find_cpu(self):
        """Device.find() sanity checks for SSD"""
        if is_cpu_temp_available():
            assert self.cpu.find().type == server.Device.DeviceType.CPU
        else:
            assert self.cpu.find().type == server.Device.DeviceType.NONE

    @mock.patch('pySMART.DeviceList')
    def test_missing_device(self, mock_pysmart_device_list,
                            mock_pysmart_devices):
        """Device.find() device not found"""
        mock_pysmart_device_list().devices = mock_pysmart_devices
        assert self.device.find().type == server.Device.DeviceType.NONE


class TestShelf:
    """Shelf tests"""

    def setup_method(self):
        """setup necessary objects
        hdds = set of server.Device which are HDD
        shelf = server.Shelf to use
        now = datetime.datetime to use to get current date
        delay = datetime.timedelta to use as standard delay
        """
        # Create HDDs
        self.hdds = set()
        hdd_list = [('SERIAL1', 'position 1'), ('SERIAL2', 'position 2')]
        for serial, position in hdd_list:
            device = mock.Mock()
            device.serial = serial
            device.position = position
            device.type = server.Device.DeviceType.HDD
            device.find.return_value = device
            self.hdds.add(device)
        hdd_temps = {0: 25, 30: 30, 35: 50, 40: 75, 41: 100}

        # Create SSDs
        self.ssds = set()
        ssd_list = [('SERIAL_A', 'position a'), ('SERIAL_B', 'position b')]
        for serial, position in ssd_list:
            device = mock.Mock()
            device.serial = serial
            device.position = position
            device.type = server.Device.DeviceType.SSD
            device.find.return_value = device
            self.ssds.add(device)
        ssd_temps = {0: 25, 50: 40, 55: 50, 60: 70, 65: 85, 70: 100}

        # Create CPU
        self.cpu = mock.Mock()
        self.cpu.serial = 'cpu'
        self.cpu.position = 'this cpu'
        self.cpu.type = server.Device.DeviceType.CPU
        self.cpu.find.return_value = self.cpu
        cpu_temps = {0: 25, 75: 40, 80: 60, 85: 80, 90: 100}

        # Create shelf
        self.devices = self.hdds | self.ssds | {self.cpu}
        self.shelf = server.Shelf('test_shelf', self.devices, 60,
                                  hdd_temps, ssd_temps, cpu_temps)

        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.delay = datetime.timedelta(hours=1)

    def test_shelf_init(self):
        """check the shelf is created properly"""
        assert self.devices == set(self.shelf)

    def test_rpm(self):
        """sanity checks for rpm property"""
        assert self.shelf.rpm == 0
        self.shelf.rpm = 2000
        assert self.shelf.rpm == 2000

    def test_negative_rpm(self):
        """rpm property: set to negative"""
        assert self.shelf.rpm == 0
        with pytest.raises(ValueError):
            self.shelf.rpm = -1
        assert self.shelf.rpm == 0

    def test_pwm_override(self):
        """pwm override sanity check"""
        assert self.shelf.pwm == 100
        self.shelf._Shelf__pwm = 50
        assert self.shelf.pwm == 50
        self.shelf.pwm = 30
        assert self.shelf.pwm == 30

    def test_pwm_bellow_0(self):
        """pwm override to <0 number"""
        with pytest.raises(ValueError):
            self.shelf.pwm = -10
        assert self.shelf.pwm == 100

    def test_pwm_above_100(self):
        """pwm override to >100 number"""
        with pytest.raises(ValueError):
            self.shelf.pwm = 150
        assert self.shelf.pwm == 100

    def test_pwm_expire(self):
        """pwm_expire sanity checks"""
        assert self.shelf.pwm_expire is None
        self.shelf.pwm_expire = self.now + self.delay
        assert self.shelf.pwm_expire == self.now + self.delay

    def test_pwm_expire_in_past(self):
        """pwm_expire with expiration in the pase"""
        with pytest.raises(ValueError):
            self.shelf.pwm_expire = self.now - self.delay
        assert self.shelf.pwm_expire is None

    def test_pwm_override_with_expiration(self):
        """pwm_override with pwm_expire in the future"""
        self.shelf.pwm = 32
        self.shelf.pwm_expire = self.now + self.delay
        assert self.shelf.pwm == 32

    def test_pwm_override_expired(self):
        """pwm_override with pwm_expire in the past"""
        self.shelf.pwm = 32
        self.shelf._Shelf__pwm_expire = self.now - self.delay
        assert self.shelf.pwm == 100

    def test_update(self):
        """update() sanity checks"""
        for hdd in self.hdds:
            hdd.temperature = 30
        next(iter(self.hdds)).temperature = 40
        for ssd in self.ssds:
            ssd.temperature = 30
        self.cpu.temperature = 30
        self.shelf.update()
        for dev in self.shelf:
            print('call 1 ', dev)
            dev.update.assert_called_once()
            print('call 1 ok ', dev)
        for dev in self.hdds.union(self.ssds):
            print('call ', dev)
            dev.update.assert_called_once()
            print('call OK ', dev)
        assert self.shelf.pwm == 75

    def test_update_ssd(self):
        """update() checks for SSD"""
        for hdd in self.hdds:
            hdd.temperature = 30
        for ssd in self.ssds:
            ssd.temperature = 30
        self.cpu.temperature = 30
        next(iter(self.ssds)).temperature = 63
        self.shelf.update()
        assert self.shelf.pwm == 70

    def test_update_cpu(self):
        """update() checks for CPU"""
        for hdd in self.hdds:
            hdd.temperature = 30
        for ssd in self.ssds:
            ssd.temperature = 30
        self.cpu.temperature = 86
        self.shelf.update()
        assert self.shelf.pwm == 80

    def test_update_low_temps(self):
        """update() checks for low temps"""
        for hdd in self.hdds:
            hdd.temperature = -10
        for ssd in self.ssds:
            ssd.temperature = -10
        self.cpu.temperature = -10
        next(iter(self.hdds)).temperature = -5
        self.shelf.update()
        assert self.shelf.pwm == 25

    def test_update_high_temps(self):
        """update() checks for high temps"""
        for hdd in self.hdds:
            hdd.temperature = 30
        for ssd in self.ssds:
            ssd.temperature = 30
        self.cpu.temperature = 86
        next(iter(self.hdds)).temperature = 1000
        self.shelf.update()
        assert self.shelf.pwm == 100


class TestHandlePing:
    """_handle_ping() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_socket):
        """sanity checks"""
        server._handle_ping(mock_socket)
        send.assert_called_once_with(mock_socket, com.Request.ACK)


class TestHandleGetPwm:
    """_handle_get_pwm() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_shelf, mock_socket):
        """sanity checks"""
        mock_shelf.pwm = 50
        server._handle_get_pwm(mock_socket, mock_shelf.identifier)
        send.assert_called_once_with(mock_socket, com.Request.SET_PWM,
                                     mock_shelf.identifier, 50)

    @mock.patch('fand.communication.send')
    def test_wrong_shelf(self, send, mock_socket):
        """wrong shelf name"""
        with pytest.raises(server.ShelfNotFoundError):
            server._handle_get_pwm(mock_socket, 'wrong_shelf')
        send.assert_not_called()


class TestHandleGetRpm:
    """_handle_get_rpm() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_shelf, mock_socket):
        """sanity checks"""
        mock_shelf.rpm = 3000
        server._handle_get_rpm(mock_socket, mock_shelf.identifier)
        send.assert_called_once_with(mock_socket, com.Request.SET_RPM,
                                     mock_shelf.identifier, 3000)

    @mock.patch('fand.communication.send')
    def test_wrong_shelf(self, send, mock_socket):
        """wrong shelf name"""
        with pytest.raises(server.ShelfNotFoundError):
            server._handle_get_rpm(mock_socket, 'wrong_shelf')
        send.assert_not_called()


class TestHandleSetRpm:
    """_handle_set_rpm() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_shelf, mock_socket):
        """sanity checks"""
        mock_shelf.rpm = 4000
        server._handle_set_rpm(mock_socket, mock_shelf.identifier, 2500)
        send.assert_called_once_with(mock_socket, com.Request.ACK)
        assert mock_shelf.rpm == 2500

    @mock.patch('fand.communication.send')
    def test_wrong_shelf(self, send, mock_shelf, mock_socket):
        """wrong shelf name"""
        mock_shelf.rpm = 4000
        with pytest.raises(server.ShelfNotFoundError):
            server._handle_set_rpm(mock_socket, 'wrong_shelf', 25000)
        send.assert_not_called()
        assert mock_shelf.rpm == 4000


class TestHandleSetPwmOverride:
    """_handle_set_pwm_override() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_shelf, mock_socket):
        """sanity checks"""
        mock_shelf.pwm = 100
        server._handle_set_pwm_override(mock_socket, mock_shelf.identifier,
                                        50)
        send.assert_called_once_with(mock_socket, com.Request.ACK)
        assert mock_shelf.pwm == 50

    @mock.patch('fand.communication.send')
    def test_wrong_shelf(self, send, mock_shelf, mock_socket):
        """wrong shelf name"""
        mock_shelf.rpm = 4000
        with pytest.raises(server.ShelfNotFoundError):
            server._handle_set_pwm_override(mock_socket, 'wrong_shelf', 25)
        send.assert_not_called()
        assert mock_shelf.rpm == 4000


class TestHandleSetPwmExpire:
    """_handle_set_pwm_expire() tests"""

    @mock.patch('fand.communication.send')
    def test_sanity(self, send, mock_shelf, mock_socket):
        """sanity checks"""
        date = mock.Mock()
        mock_shelf.pwm_expire = None
        server._handle_set_pwm_expire(mock_socket, mock_shelf.identifier,
                                      date)
        send.assert_called_once_with(mock_socket, com.Request.ACK)
        assert mock_shelf.pwm_expire == date

    @mock.patch('fand.communication.send')
    def test_wrong_shelf(self, send, mock_shelf, mock_socket):
        """wrong shelf name"""
        date = mock.Mock()
        mock_shelf.pwm_expire = None
        with pytest.raises(server.ShelfNotFoundError):
            server._handle_set_pwm_expire(mock_socket, 'wrong_shelf', date)
        send.assert_not_called()
        assert mock_shelf.pwm_expire is None


class TestListenClient:
    """listen_client() tests"""

    @mock.patch('fand.communication.recv')
    def test_sanity(self, mock_recv, mock_socket):
        """sanity checks"""
        mock_ping = mock.Mock()
        server.REQUEST_HANDLERS[com.Request.PING] = mock_ping
        mock_ping.side_effect = lambda *_: com.reset_connection(mock_socket)
        mock_recv.return_value = (com.Request.PING, ())
        server.listen_client(mock_socket)
        mock_recv.assert_called_once_with(mock_socket)
        mock_ping.assert_called_once_with(mock_socket)
        assert not com.is_socket_open(mock_socket)

    @mock.patch('fand.communication.recv')
    def test_handler_not_found(self, mock_recv, mock_socket):
        """wrong request from recv"""
        mock_recv.return_value = ('wrong request', ())
        server.listen_client(mock_socket)
        mock_recv.assert_called_once_with(mock_socket)
        assert not com.is_socket_open(mock_socket)


class TestReadConfigTemps:
    """_read_config_temps() tests"""
    TEST_VALUES = {
        ' 0: 25, 37: 30, 38: 40, 39: 50, 40: 75, 41: 100':
        {0: 25, 37: 30, 38: 40, 39: 50, 40: 75, 41: 100},
        '0:25,60:40,62.5:50,65:70,67.5:90,70:100':
        {0: 25, 60: 40, 62.5: 50, 65: 70, 67.5: 90, 70: 100},
    }

    def test_sanity(self):
        """sanity checks"""
        for test_str, test_result in type(self).TEST_VALUES.items():
            assert server._read_config_temps(test_str) == test_result


class TestFindConfigFile:
    """_find_config_file() tests"""

    @mock.patch.dict('os.environ', clear=True)
    @mock.patch('os.path.isfile')
    def test_not_found(self, mock_isfile):
        """Test with no config file"""
        mock_isfile.return_value = False
        assert server._find_config_file() is None

    @mock.patch.dict('os.environ', clear=True)
    @mock.patch('os.path.isfile')
    def test_etc_config(self, mock_isfile):
        """Test for /etc/fand.ini"""
        def do_isfile(filename, *_):
            if filename == '/etc/fand.ini':
                return True
            return False
        mock_isfile.side_effect = do_isfile
        assert server._find_config_file() == '/etc/fand.ini'

    @mock.patch.dict('os.environ', clear=True)
    @mock.patch('os.path.isfile')
    def test_cwd_config(self, mock_isfile):
        """Test for ./fand.ini"""
        def do_isfile(filename, *_):
            if filename in ['/etc/fand.ini', './fand.ini']:
                return True
            return False
        mock_isfile.side_effect = do_isfile
        assert server._find_config_file() == './fand.ini'

    @mock.patch.dict('os.environ', {'FAND_CONFIG': 'fand config'}, clear=True)
    @mock.patch('os.path.isfile')
    def test_env_config(self, mock_isfile):
        """Test for FAND_CONFIG environment variable"""
        def do_isfile(filename, *_):
            if filename in ['/etc/fand.ini', './fand.ini']:
                return True
            return False
        mock_isfile.side_effect = do_isfile
        assert server._find_config_file() == 'fand config'
