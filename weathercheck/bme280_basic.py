import math
import time

import bme280
import smbus2

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)


def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5) + 32


# BME280 sensor address (default address)
def get_data(address=0x77):
    b = 17.62
    c = 243.12

    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        # Extract temperature, pressure, and humidity
        temp_c = data.temperature
        pres = data.pressure
        hum = data.humidity

        # Convert temperature to Fahrenheit
        temp_f = celsius_to_fahrenheit(temp_c)
        gamma = (b * temp_c / (c + temp_c)) + math.log(hum / 100.0)
        dewpoint = (c * gamma) / (b - gamma)

    except Exception as e:
        print("An unexpected error occurred:", str(e))
        temp_c = math.nan
        temp_f = math.nan
        dewpoint = math.nan
        hum = math.nan
        pres = math.nan

    return temp_c, temp_f, dewpoint, hum, pres


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
