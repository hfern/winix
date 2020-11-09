# Winix Controller

This is a Python library for controlling Winix C545 Air Purifier
devices. I reverse-engineered the API calls from the Android app. There
are a few weird idiosyncrasies with the Winix backends.

Included in this package is a CLI program `winixctl`.

## Setup

Install using PyPI: `pip install winix`.
You then have access to the `winix` module in python as well
as the `winixctl` command for shell (which uses the library).

## `winixctl` CLI

```
~/dev/winix(master) » winixctl
usage: winixctl [-h] {login,refresh,devices,fan,power,mode,plasmawave} ...

Winix C545 Air Purifier Control

positional arguments:
  {login,refresh,devices,fan,power,mode,plasmawave}
    login               Authenticate Winix account
    refresh             Refresh account device metadata
    devices             List registered Winix devices
    fan                 Fan speed controls
    power               Power controls
    mode                Mode controls
    plasmawave          Plasmawave controls

optional arguments:
  -h, --help            show this help message and exit
```

In order to control your device, you first must run `winixctl login`.
this will save a token from the Winix backend in a file on your system
at `~/config/winix/config.json`. It will prompt you for a username
and password. You can use the `--username` and `--password` flags as well.

You can see the devives registered to your winix account
with `winixctl devices`.

    ~/dev/winix(master*) » winixctl devices
    1 devices:
    Device#0 (default) -------------------------------
          Device ID : 123456abcde_********** (hidden)
                Mac : 123456abcde
              Alias : Bedroom
           Location : SROU

    Missing a device? You might need to run refresh.

The last portion of the Device ID is hidden as it can be used to control
the device.
