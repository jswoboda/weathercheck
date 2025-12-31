import time

from weathercheck import get_bme280_data

if __name__ == "__main__":
    while True:
        try:
            temp_c, temp_f, dewpoint, dewpoint_f, hum, pres, ts = get_bme280_data()

            # Print the readings
            print(f"Time of reading: {0}".format(ts))
            print("Temperature: {:.2f} °C, {:.2f} °F".format(temp_c, temp_f))
            print("Pressure: {:.2f} hPa".format(pres))
            print("Humidity: {:.2f} %".format(hum))
            print("Dewpoint: {:.2f} °C, {:.2f} °F".format(dewpoint, dewpoint_f))
            # Wait for a few seconds before the next reading
            time.sleep(2)
        except KeyboardInterrupt:
            print("Program stopped")
            break
        except Exception as e:
            print("An unexpected error occurred:", str(e))
