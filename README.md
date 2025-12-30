# weathercheck
Experiment using MQTT and iotdb

## Setup 

* Create a conda environment and keep track of the name
* Install the following libraries
  * matplotlib
  * pandas
  * adafruit-blinka
  * adafruit-circuitpython-gps
  * adafruit-circuitpython-bme280
* Run the setup.py 
  
``` bash
pip setup.py -e .
```
* Edit the weatherrecord.service and weatherservice.sh files to point to the correct paths and conda libraries. Also `chmod +x bin/weatherservice.sh'
* Copy weatherrecoord.service to `~/.config/systemd/user/weatherrecord.service`
* Run `systemctl --user list-unit-files` to see if it's copied over.
* To start the service run the following:

```
systemctl --user enable weatherrecord.service
systemctl --user start weatherrecord.service
```

* `journalctl -r --user-unit weatherrecord.service` (or `tail -f /var/log/syslog`)
* To run on boot 

```
sudo loginctl enable-linger $USER
```

To stop and disable service

```
systemctl --user stop weatherrecord.service
systemctl --user disable weatherrecord.service
```

## Notes 

When using the gps module from adafruit the serial port is not always `/dev/ttyUSB0` if using the USB-C version of the module. It should be in the `/dev/serial/` directory and will require some digging and trial and error.
