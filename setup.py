"""Simple daemon to control fan speed"""

import setuptools

from fand import (__version__, __author__, __email__, __license__, __url__,
                  __doc__)

setuptools.setup(
    name='fand',
    version=__version__,
    description=__doc__,
    long_description=open('README.md', 'r').read(),
    long_description_content_type='test/markdown',

    author=__author__,
    author_email=__email__,
    license=__license__,
    url=__url__,

    python_requires='>=3, <4',
    install_requires=[],
    extras_require={
        'dev': ['flake8'],
        'server': ['pySMART'],
        'clientrpi': ['gpiozero'],
        'clientrpi-rpi-gpio': ['RPi.GPIO'],
        'clientrpi-pigpio': ['pigpio'],
        'clientrpi-rpio': ['RPIO'],
    },

    packages=['fand'],
    entry_points={
        'console_scripts': [
            'fanctl = fand.fanctl:main',
            'fand-server = fand.server:main',
            'fand-clientrpi = fand.clientrpi:main',
        ],
    },
    scripts=['bin/fand'],

    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
    ],
)
