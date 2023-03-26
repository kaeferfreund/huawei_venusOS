# huawei_venusOS
a venusOS driver for huawei sun2000 inverters

### Purpose

This service is meant to be run on a raspberry Pi with Venus OS from Victron.

The Python script cyclically reads data from the huawei inverter via modbus TCP and publishes information on the dbus, using the service name com.victronenergy.pvinverter. This makes the inverter appear on Venus OS and VRM

### Configuration

In the Python file, you should put the IP of your inverter

### Installation

1. Copy the files to the /data folder on your venus:

2. test via `python3 huawei.py`

3. Copy the services/run file  to `/opt/victronenergy/service/dbus-huawei` it will be copied to /services/dbus-huawei after each restart and will survive updates

4. Restart to initiate the copy process
