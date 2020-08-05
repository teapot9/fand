# Simple daemon to control fan speed

Control fan speed according to drive temperatures.

## Introduction

The purpose of this program is to allow controlling the fan speed of a server
from another one.
One server checks drive temperatures.
Multiple clients ask the fan speed they should set and use PWM to change it.

This program also wants to be cross-platform.
It should work with Linux and FreeBSD, as they are the platform used for
testing.
While they have not been tested, it should also works on
\*BSD, Mac OS and Windows.

This program contain multiples modules:
 * server: daemon monitoring drives
    * listen for connection from clients and answer their requests
    * monitor drives temperatures and defines a fan speed percentage
      corresponding to the hottest drive
 * fanctl: cli to interract with the server
    * send a single request to a server
 * clientrpi: Raspberry Pi daemon controlling fans
    * Get fan speed from the server, change the PWM signal accordingly
    * Send to the server the RPM input from the fans

## fand CLI

This program install 4 scripts:
 * fand: global executable to start any modules.
   Syntax: `fand MODULE MODULE_ARGS`
 * fand-server: equivalent to `fand server`
 * fand-clientrpi: equivalent to `fand clientrpi`
 * fanctl: equivalent to `fand fanctl`

## Server

The server group drives by shelves.
One shelf contains a list of drives.
For each shelf the server find the highest drive temperature to get the
corresponding fan speed.
The fan speed is assigned to the shelf, ready to be given to any client
asking for it.

### Configuration

The `[DEFAULT]` section contains the default configuration for all shelves.
It must contain a `shelves` key listing the shelves names.
Each shelf must have a section with its name.

See the `fand.ini.example` to get a description of the configuration.

### Usage

The server listen by default on the interface corresponding to
the hostname, on port 9999.
Configuration file is searched in order:
 - `FAND_CONFIG` environment variable
 - `./fand.ini`
 - `/etc/fand.ini`

Some command line examples:
 - `fand server` start with default configuration
 - `fand-server` does the same
 - `fand-server -vvv` enable very verbose
 - `fand server -a 0.0.0.0 -p 1234 -c ./config.ini` listen on all interfaces
   on port 1234, use configuration file ./config.ini

## Raspberry Pi client

### Usage

The client connect by default to `HOSTNAME:9999`.
The GPIO pin for the PWM signal output is configurable with the `-P` parameter,
the GPIO pin for the RPM tachometer input with the `-r` parameter.

gpiozero uses Broadcom (BCM) pin numbering for the GPIO pins,
as opposed to physical (BOARD) numbering.
See the
[gpiozero documentation](https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering)
for more information.

Example of command lines:
 - `fand-clientrpi` start with default configuration
 - `fand clientrpi -a server-name.local -p 1234 -P 3 -r 2` connect to
   server-name.local on port 1234, use GPIO pin 3 for PWM output
   and GPIO pin 2 for RPM input

## Fanctl

Send a request to a fand server.

### Usage

Example of command lines:
 - `fanctl ping` ping the server, use default configuration
 - `fanctl -a 10.0.1.4 shelfpwm myshelf` get the shelf PWM percentage of
   the shelf named "myshelf"

## Dependencies

Python support:
 * Should support any python 3 version supported by
   [upstream](https://www.python.org/downloads/).

OS support:
 * server: same as pySMART, officially supporting Linux, Windows and FreeBSD
 * fanctl: should support Linux, \*BSD, Windows and Mac OS
 * clientrpi: same as gpiozero, officially supporting Linux, Windows and Mac OS

Python dependencies for modules:
 * server:
   * [pySMART](https://pypi.org/project/pySMART/)
     ([upstream](https://github.com/freenas/py-SMART)):
     access drive SMART informations
 * clientrpi:
   * [gpiozero](https://pypi.org/project/gpiozero/)
     ([upstream](https://github.com/gpiozero/gpiozero)):
     GPIO interraction for PWM and RPM signals
   * gpiozero's native pin factory does not currently (aug 2020) supports PWM,
     you need one of the following packages:
     * [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)
       ([upstream](https://sourceforge.net/projects/raspberry-gpio-python/)):
       does not supports hardware PWM, only uses software PWM
     * [pigpio](https://pypi.org/project/pigpio/)
       ([upstream](http://abyz.me.uk/rpi/pigpio/python.html)):
       supports hardware PWM but cannot work with Linux's lockdown LSM
     * [RPIO](https://pypi.org/project/RPIO/)
       ([upstream](https://github.com/metachris/RPIO)):
       unmaintained

Non-python dependencies for modules:
 * server:
   * [smartmontools](https://www.smartmontools.org/):
     pySMART's backend

## Installation

### Server

Install smartmontools on your system with your prefered package manager.

Install fand with:
```pip install fand[server]```

### Fand controller (fanctl)

Install fand with:
```pip install fand```

### Raspberry Pi client

Install fand with one of the following commands:
 * Install with RPi.GPIO:
   ```pip install fand[clientrpi,clientrpi-rpi-gpio]```
 * Install with pigpio:
   ```pip install fand[clientrpi,clientrpi-pigpio]```
 * Install with RPIO:
   ```pip install fand[clientrpi,clientrpi-rpio]```

### Custom installation

You can cumulate the extra dependencies if you want multiple modules.
```pip install fand[server,clientrpi]```

