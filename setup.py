#!/usr/bin/env python
"""
setup.py
This is the setup file for the weathercheck python package

@author: John Swoboda
"""

from pathlib import Path

from setuptools import find_packages, setup

req = [
    "numpy",
    "schedule",
    "filetype",
    "scipy",
    "matplotlib",
    "pandas",
    "adafruit-blinka",
    "adafruit-circuitpython-gps",
    "adafruit-circuitpython-bme280",
]
scripts = [
    "bin/run_weather.py",
]


config = dict(
    description="Recording remort weather data. ",
    author="John Swoboda",
    url="https://github.com/jswoboda/weathercheck",
    version="1.0",
    install_requires=req,
    python_requires=">=3.0",
    packages=find_packages(),
    scripts=scripts,
    name="weathercheck",
)

setup(**config)
