"""fand.util tests"""

import unittest.mock as mock

import pytest

util = pytest.importorskip('fand.util')


class TestTerminate:
    """terminate() tests"""

    def teardown_method(self):
        """clear TERMINATE flag"""
        util.__TERMINATE__ = False

    def test_sanity(self):
        """sanity checks"""
        assert not util.terminating()
        with pytest.raises(SystemExit):
            util.terminate()
        assert util.terminating()


class TestSleep:
    """sleep() tests"""

    @mock.patch('time.sleep')
    def test_sanity(self, mock_sleep):
        """sanity checks"""
        util.sleep(6.5)
        total = 0
        for args, _ in mock_sleep.call_args_list:
            total += args[0]
        assert total == 6.5

    @mock.patch('time.sleep')
    def test_terminate(self, mock_sleep):
        """check when terminate() is called during sleep"""
        def term(*_):
            try:
                util.terminate()
            except SystemExit:
                pass
        mock_sleep.side_effect = term
        util.sleep(6)
        assert util.terminating()
        mock_sleep.assert_called_once()
        util.__TERMINATE__ = False
