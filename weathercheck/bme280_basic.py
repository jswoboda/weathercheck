import math
import time
from datetime import datetime, timezone

import bme280
import smbus2

# Initialize I2C bus
bus = smbus2.SMBus(1)


def celsius_to_fahrenheit(celsius):
    """Convert degrees C to degrees F for those animals in America.

    Parameters
    ----------
    celsius : float
        Input in degrees C.

    Returns
    -------
    : float
        In degrees F.
    """
    return (celsius * 9 / 5) + 32


# BME280 sensor address (default address)
def get_bme280_data(address=0x77):
    """Reads the info from the BME280 sensor.

    Parameters
    ----------
    address : int
        Integer address for the I2C input.

    Returns
    -------
    temp_c : float
        Temperature in C.
    temp_f : float
        Temperature in F.
    dewpoint : float
        Dewpoint in degrees C.
    dewpoint_f : float
        Dewpoint in degrees F.
    hum : float
        Humidity in percentage.
    pres : float
        Presure in hPa.
    ts : datetime
        Timestamp of measurement.
    """
    # Load calibration parameters
    calibration_params = bme280.load_calibration_params(bus, address)
    b = 17.62
    c = 243.12

    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        ts = data.timestamp
        # Extract temperature, pressure, and humidity
        temp_c = data.temperature
        pres = data.pressure
        hum = data.humidity

        # Convert temperature to Fahrenheit
        temp_f = celsius_to_fahrenheit(temp_c)
        gamma = (b * temp_c / (c + temp_c)) + math.log(hum / 100.0)
        dewpoint = (c * gamma) / (b - gamma)
        dewpoint_f = celsius_to_fahrenheit(dewpoint)
    except Exception as e:
        print("An unexpected error occurred:", str(e))
        temp_c = math.nan
        temp_f = math.nan
        dewpoint = math.nan
        dewpoint_f = math.nan
        hum = math.nan
        pres = math.nan
        ts = datetime.now().astimezone(timezone.utc)

    return temp_c, temp_f, dewpoint, dewpoint_f, hum, pres, ts


if __name__ == "__main__":
    while True:
        try:
            temp_c, temp_f, dewpoint, hum, pres = get_data()

            # Print the readings
            print("Temperature: {:.2f} °C, {:.2f} °F".format(temp_c, temp_f))
            print("Pressure: {:.2f} hPa".format(pres))
            print("Humidity: {:.2f} %".format(hum))
            print("Dewpoint: {:.2f} %".format(dewpoint))
            # Wait for a few seconds before the next reading
            time.sleep(2)
        except KeyboardInterrupt:
            print("Program stopped")
            break
        except Exception as e:
            print("An unexpected error occurred:", str(e))
