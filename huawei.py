# Description: This is a python script to read data from a Huawei Sun2000 inverter via Modbus TCP
# https://github.com/olivergregorius/sun2000_modbus
from sun2000_modbus import inverter
from sun2000_modbus import registers

# https://github.com/victronenergy/venus/wiki/howto-add-a-driver-to-Venus

from vedbus import VeDbusService
from dbus.mainloop.glib import DBusGMainLoop
try:
    import gobject  # Python 2.x
except:
    from gi.repository import GLib as gobject  # Python 3.x
import dbus
import dbus.service
import sys
import os
import platform

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(
    __file__), '/opt/victronenergy/dbus-modem'))

# Again not all of these needed this is just duplicating the Victron code.


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
DBusGMainLoop(set_as_default=True)


class modbusQuerry:
    
    def __init__(self):
        self.thisInverter = inverter.Sun2000(host='192.168.169.38', port=502, unit=1)
        self.thisInverter.connect()
        print("intialising")
        
    def _readData(self):
            self.thisInverter.connect()
            
            if(self.thisInverter.connected == False):
                return True
        
            # pv inverter
            self.ac_c1 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseACurrent)
            self.ac_c2 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseBCurrent)
            self.ac_c3 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseCCurrent)
            self.ac_v1 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseAVoltage)
            self.ac_v2 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseBVoltage)
            self.ac_v3 = self.thisInverter.read(registers.InverterEquipmentRegister.PhaseCVoltage)
            self.pf = self.thisInverter.read(registers.InverterEquipmentRegister.PowerFactor)
            self.power = self.thisInverter.read(registers.InverterEquipmentRegister.InputPower)
            self.energy = self.thisInverter.read(registers.InverterEquipmentRegister.AccumulatedEnergyYield)
            
            print("power: " + str(self.power))
            
            return True

    def _update(self):
            
            if(self.thisInverter.connected == False):
                dbusservice['pvinverter.pv0']['/Ac/L1/Power'] = 0
                dbusservice['pvinverter.pv0']['/Ac/L2/Power'] = 0
                dbusservice['pvinverter.pv0']['/Ac/L3/Power'] = 0
                dbusservice['pvinverter.pv0']['/Ac/Power'] = 0
                print("not connected")
                return True
        
            # pv inverter
            if(self.ac_c1 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L1/Current'] = self.ac_c1
            
            if(self.ac_c2 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L2/Current'] = self.ac_c2
            if(self.ac_c3 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L3/Current'] = self.ac_c3

            if(self.ac_v1 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L1/Voltage'] = self.ac_v1


            if(self.ac_v2 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L2/Voltage'] = self.ac_v2
            if(self.ac_v3 is not None):
                dbusservice['pvinverter.pv0']['/Ac/L3/Voltage'] = self.ac_v3

            
            if(self.power is not None): 
                dbusservice['pvinverter.pv0']['/Ac/Power'] = self.power

            if(self.ac_v1  is not None and self.ac_c1 is not None and self.pf is not None):
                self.ac_p1 = self.ac_v1*self.ac_c1*self.pf
                if(self.ac_p1 > self.power/3):
                    self.ac_p1 = self.power/3
                dbusservice['pvinverter.pv0']['/Ac/L1/Power'] = self.ac_p1
                
            if(self.ac_v2 is not None and self.ac_c2 is not None and self.pf is not None): 
                self.ac_p2 = self.ac_v2*self.ac_c2*self.pf
                if(self.ac_p2 > self.power/3):
                    self.ac_p2 = self.power/3
                dbusservice['pvinverter.pv0']['/Ac/L2/Power'] = self.ac_p2
                
            if(self.ac_v3 is not None and self.ac_c3 is not None and self.pf is not None): 
                self.ac_p3 = self.ac_v3*self.ac_c3*self.pf
                if(self.ac_p3 > self.power/3):
                    self.ac_p3 = self.power/3
                dbusservice['pvinverter.pv0']['/Ac/L3/Power'] = self.ac_p3

            if(self.energy is not None): 
                dbusservice['pvinverter.pv0']['/Ac/Energy/Forward'] = self.energy
                dbusservice['pvinverter.pv0']['/Ac/L1/Energy/Forward'] = round(self.energy/3.0, 2)
                dbusservice['pvinverter.pv0']['/Ac/L2/Energy/Forward'] = round(self.energy/3.0, 2)
                dbusservice['pvinverter.pv0']['/Ac/L3/Energy/Forward'] = round(self.energy/3.0, 2)
            
            return True
    # -----------------------------
    # Here is the bit you need to create multiple new services - try as much as possible timplement the Victron Dbus API requirements.


def new_service(base, type, physical, id, instance):
    self = VeDbusService("{}.{}.{}_id{:02d}".format(
        base, type, physical,  id), dbusconnection())

    # Create the management objects, as specified in the ccgx dbus-api document
    # Supported paths:
    # https://github.com/victronenergy/venus/wiki/dbus#generic-paths
    self.add_path('/Mgmt/ProcessName', __file__)
    self.add_path('/Mgmt/ProcessVersion',
                  'Unknown version, and running on Python ' + platform.python_version())
    self.add_path('/Connected', 1)
    self.add_path('/HardwareVersion', 0)

    def _kwh(p, v): return (str(v) + 'kWh')

    def _a(p, v): return (str(v) + 'A')

    def _w(p, v): return (str(v) + 'W')
    def _v(p, v): return (str(v) + 'V')
    def _c(p, v): return (str(v) + 'C')

    if physical == 'pvinverter':

            # Supported paths:
            # https://github.com/victronenergy/venus/wiki/dbus#pv-inverters
            self.add_path('/DeviceInstance', instance)
            self.add_path('/FirmwareVersion', "Unknown")
            # value used in self.ac_sensor_bridge.cpp of dbus-cgwacs
            self.add_path('/ProductId', "Unknown")
            self.add_path('/ProductName', "Huawei SUN2000")
            self.add_path('/Ac/Energy/Forward', None, gettextcallback=_kwh)
            self.add_path('/Ac/L1/Energy/Forward', None, gettextcallback=_kwh)
            self.add_path('/Ac/L2/Energy/Forward', None, gettextcallback=_kwh)
            self.add_path('/Ac/L3/Energy/Forward', None, gettextcallback=_kwh)
            self.add_path('/Ac/Power', None, gettextcallback=_w)
            self.add_path('/Ac/L1/Current', None, gettextcallback=_a)
            self.add_path('/Ac/L2/Current', None, gettextcallback=_a)
            self.add_path('/Ac/L3/Current', None, gettextcallback=_a)
            self.add_path('/Ac/L1/Power', None, gettextcallback=_w)
            self.add_path('/Ac/L2/Power', None, gettextcallback=_w)
            self.add_path('/Ac/L3/Power', None, gettextcallback=_w)
            self.add_path('/Ac/L1/Voltage', None, gettextcallback=_v)
            self.add_path('/Ac/L2/Voltage', None, gettextcallback=_v)
            self.add_path('/Ac/L3/Voltage', None, gettextcallback=_v)
            self.add_path('/Ac/MaxPower', None, gettextcallback=_w)
            self.add_path('/ErrorCode', None)
            self.add_path('/Position', 0)
            self.add_path('/StatusCode', None)

            return self


dbusservice = {}  # Dictonary to hold the multiple services

Querry = modbusQuerry()

# service defined by (base*, type*, id*, instance):
# * items are include in service name
# Create all the dbus-services we want
dbusservice['pvinverter.pv0'] = new_service(
    'com.victronenergy', 'pvinverter.pv0', 'pvinverter', 0, 20)

# Everything done so just set a time to run an update function to update the data values every 1 second
gobject.timeout_add(10000, Querry._update)

print("Connected to dbus, and switching over to gobject.MainLoop() (= event based)")
mainloop = gobject.MainLoop()
mainloop.run()

if __name__ == "__main__":
    try:
        Querry._readData()
    except Exception as ex:
        print("Issues querying Inverter -ERROR :", ex)
