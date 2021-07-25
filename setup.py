"""Simple daemon to control fan speed"""

import setuptools

import fand

setuptools.setup(
    name=fand.__name__,
    version=fand.__version__,
    description=fand.__doc__,
    long_description=open('README.rst', 'r').read(),
    long_description_content_type='text/x-rst',

    author=fand.__author__,
    author_email=fand.__email__,
    license=fand.__license__,
    license_files=['LICENSE'],
    url=fand.__url__,

    python_requires='>=3.6, <4',
    install_requires=[],
    extras_require={
        'test': ['pytest'],
        'qa': ['flake8', 'flake8-import-order', 'mypy', 'tox'],
        'doc': ['sphinx', 'sphinx-rtd-theme'],
        'server': ['pySMART', 'psutil'],
        'clientrpi-base': ['gpiozero'],
        'clientrpi-rpi-gpio': ['gpiozero', 'RPi.GPIO'],
        'clientrpi-pigpio': ['gpiozero', 'pigpio'],
        'clientrpi-rpio': ['gpiozero', 'RPIO'],
    },

    packages=['fand'],
    entry_points={
        'console_scripts': [
            'fand = fand.__main__:entry_fand',
            'fanctl = fand.fanctl:main',
            'fand-server = fand.server:main',
            'fand-clientrpi = fand.clientrpi:main',
        ],
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
        "Typing :: Typed",
    ],
    keywords=['fan-control', 'daemon', 'hardware', 'raspberry-pi', 'gpio',
              'monitoring', 'temperature-monitoring', 'pysmart', 'gpiozero'],
    platforms=['Linux', 'FreeBSD'],
)
