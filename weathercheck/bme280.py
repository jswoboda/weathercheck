import math

import board
from adafruit_bme280 import basic as adafruit_bme280


def get_env_data():
    b = 17.62
    c = 243.12

    i2c = board.I2C()  # uses board.SCL and board.SDA

    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, 0x77)
    bme280.sea_level_pressure = 1013.4

    gamma = (b * bme280.temperature / (c + bme280.temperature)) + math.log(
        bme280.humidity / 100.0
    )
    dewpoint = (c * gamma) / (b - gamma)

    return (
        bme280.temperature,
        bme280.humidity,
        bme280.pressure,
        bme280.altitude,
        dewpoint,
    )


print("\nTemperature: %0.1f C" % bme280B.temperature)
print("Humidity: %0.1f %%" % bme280B.humidity)
print("Pressure: %0.1f hPa" % bme280B.pressure)
print("Altitude = %0.2f meters" % bme280B.altitude)
print("Dew point = %0.1f" % dewpoint)
