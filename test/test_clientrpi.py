"""fand.clientrpi tests"""

import unittest.mock as mock

import pytest

client = pytest.importorskip('fand.clientrpi')


@pytest.fixture(autouse=True)
def cleanup_gpio():
    """Remove gpio devices from the list of known GPIO defices"""
    yield
    client.__GPIO_DEVICES__ = set()


class TestGpioRpm:
    """GpioRpm class tests"""

    def setup_method(self):
        """setup GpioRpm object
        rpm = GpioRpm
        mock_button = corresponding gpiozero.Button
        """
        with mock.patch('gpiozero.Button') as mock_button:
            self.rpm = client.GpioRpm(10)
            self.mock_button = mock_button

    def test_pressed(self):
        """check GpioRpm.__pressed()"""
        assert self.rpm._GpioRpm__count == 0
        self.rpm._GpioRpm__pressed()
        assert self.rpm._GpioRpm__count == 1

    def test_update(self):
        """check GpioRpm.update()"""
        assert self.rpm.rpm == 0
        self.rpm._GpioRpm__count = 1000
        self.rpm._GpioRpm__start_time = 1000
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = 1010
            self.rpm.update()
        assert self.rpm.rpm == 3000


class TestGpioPwm:
    """GpioPwm class tests"""

    def setup_method(self):
        """setup GpioPwm object
        pwm = GpioPwm
        mock_led = corresponding gpiozero.PWMLED
        """
        with mock.patch('gpiozero.PWMLED') as mock_led:
            self.pwm = client.GpioPwm(10)
            self.pwm._GpioPwm__gpio.value = 1
            self.mock_led = mock_led

    def test_set_pwm(self):
        """sanity check for setting pwm"""
        assert self.pwm.pwm == 100
        self.pwm.pwm = 50
        assert self.pwm.pwm == 50

    def test_pwm_too_high(self):
        """give pwm above 100"""
        with pytest.raises(ValueError):
            self.pwm.pwm = 110
        assert self.pwm.pwm == 100

    def test_pwm_negative(self):
        """give negative pwm"""
        with pytest.raises(ValueError):
            self.pwm.pwm = -4
        assert self.pwm.pwm == 100
