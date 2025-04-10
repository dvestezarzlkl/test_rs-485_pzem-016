from typing import Union
import struct,serial
from lib.helper import getCrc, bytePrint


_general_addr:int = 0xF8  # General address for calibration
"""General address for calibration, used for factory calibration and return to factory maintenance occasions."""

addr_default:int = _general_addr
addr_broadcast = 0x00  # Broadcast address

port:str = 'COM3'
"""Serial port name (e.g., 'COM3' for Windows or '/dev/ttyUSB0' for Linux)"""

baudRate:int = 9600
"""Baud rate for the serial communication"""

timeOut:int = 1
"""Timeout for the serial communication in seconds"""

fn_r_hold_reg = 0x03  # Read Holding Register
fn_r_in_reg = 0x04  # Read Input Register
fn_w_reg = 0x06  # Write Single register
fn_calibrate = 0x41  # Calibration
fn_reset_energy = 0x42  # Reset energy


debug:bool = False

class masterData:
    voltage: int = 0
    """ 2B
    1register = 0.1V
    """
    
    current: int = 0
    """ 4B
    2 register Current Low 16 reg / High 16 reg, 1LSB = 0,001A
    """
    
    power: int = 0
    """ 4B
    Power 2 register (same as current) 1LSB = 0.1W
    """
    
    energy: int = 0
    """ 4B
    Energy 2 register (same as current) 1LSB = 1Wh
    """
    
    frequency: int = 0
    """ 2B
    Frequency 1 register 1LSB = 0.1Hz
    """
    
    pf: int = 0
    """ 2B
    Power factor 1 register 1LSB = 0.01
    """
    
    alarm: bool = False
    """ 2B
    Alarm 1 register - 0xFFFF = alarm (true), 0x0000 = no alarm (false)
    """

    def __from_bytes(self, data: bytes, addr:int=0)->None:
        """Convert bytes to masterData object.
        
        Args:
            data (bytes): Data to convert.
            addr (int, optional): The register address which is read. Defaults to 0.
        
        """
        
        # vyplníme r 20ti bajty 0x00
        r = bytearray(20)
        # ofset od regnum
        offset = addr * 2
        ln=len(data)
        # zkontrolujeme zda ln nepřesáhne 20B z ofsetu
        if ln > 20 - offset:
            ln = 20 - offset        
        r[offset:offset+ln] = data[0:ln]  # přečteme do struktury správně, tzn pokud není adr0 tak se musí o to posunout
        
        # nastavíme property
        
        # volty
        self.voltage = struct.unpack('>H', r[0:2])[0]  # 2B
        self.voltage = self.voltage * 0.1  # 1LSB = 0.1V
        
        # proud 4B
        self.current = struct.unpack('>HH', r[2:6])  # 2x 2B
        self.current = (self.current[0] + (self.current[1] << 16)) * 0.001  # 1LSB = 0.001A
        
        # výkon 4B
        self.power = struct.unpack('>HH', r[6:10])  # 2x 2B
        self.power = (self.power[0] + (self.power[1] << 16)) * 0.1  # 1LSB = 0.1W
        
        # energie 4B
        self.energy = struct.unpack('>HH', r[10:14])  # 2x 2B
        self.energy = (self.energy[0] + (self.energy[1] << 16))  # 1LSB = 1Wh
        
        # frekvence 2B
        self.frequency = struct.unpack('>H', r[14:16])[0]  # 2B
        self.frequency = self.frequency * 0.1  # 1LSB = 0.1Hz
        
        # power factor 2B
        self.pf = struct.unpack('>H', r[16:18])[0]  # 2B
        self.pf = self.pf * 0.01  # 1LSB = 0.01
        
        # alarm 2B
        self.alarm = struct.unpack('>H', r[18:20])[0]  # 2B
        # alarm = 0xFFFF = alarm (true), 0x0000 = no alarm (false)
        if self.alarm == 0xFFFF:
            self.alarm = True
        else:
            self.alarm = False
        
    # adr bude none,int nebo tuple takže typ bude int|tuple, vytvoř typ který může být tyto dva tzn addr:Union[int,tuple]
    def requestData(self,addr:int=None,regId:Union[int,tuple]=0,count=0x0A)->bool:
        """Read all registers from the meter and return booleaning if the read was successful. 
        If return is True, the object will be updated with the read data.
        
        Args:
            addr (int, optional): The address of the meter. Defaults to None.
            regId (int|tuple, optional): The register address to read. Defaults to 0, 0 - 9.
                if tuple is passed, it will be used as (register addr, register count). 'Register count' will be used as 'ln' anf parameter 'ln' will be ignored.  
                Example: obj.requestData(registers.voltage) will read voltage register only and ignore 'ln' parameter, other properties will be set to 0.
            count (int, optional): The number of registers to read. Defaults to 0x0A - all registers.
        
        Returns:
            bool: True if the read was successful, False otherwise.
            This object will be updated with the read data.
            
        Throws:
            TypeError: If the address is not an integer.
            ValueError: If the address is not in the range 0x01 to 0xF7.                                    
            
        """
        if addr is None:
            addr = addr_default
        
        if isinstance(regId, tuple):
            # unpack tuple into addr and count
            regId, count = regId
        
        # Create a bytearray for the request <1B addr>, <1B fn_r_in_reg>, <2B register>, <2B number of reg>, <2B CRC>
        # přečteme celý blok dat tj registry 0 - 9 (20 bajtů = 10x uint16)
        request = bytearray([
            addr,
            fn_r_in_reg,
            (regId >> 8) & 0xFF,  # Register address high byte
            (regId & 0xFF),  # Register address low byte
            (count >> 8) & 0xFF,  # Number of registers high byte
            (count & 0xFF),  # Number of registers low byte
        ])
        
        if debug:
            print(" ---------- Data Request ----------")
            print(" -- Data to send:", bytePrint(request))
            print(" -- Data length:", len(request))
            print(" -- Address:", addr)
            print(" -- Function code:", fn_r_in_reg)
            
        exp_len = (count*2) + 5  # expected length of response, 5= slaveAdr + fn code + len + crc
        if debug:
            print(" -- Expected response length:", exp_len)
        
        data, crc_received, crc_ok, fn_code, r_addr = self.__sendAndRcv(request, exp_len)
        if data is None:
            return False
   
        # otestujeme návratová data
        if fn_code != fn_r_in_reg and r_addr != addr:
            if debug:
                print(" !! Invalid response")
            return False
        if not crc_ok:
            if debug:
                print(" !! CRC check failed")
            
        # načteme data
        self.__from_bytes(data, regId)

        if debug:
            print(" -- Data received successfully")
            print(" -- Data length:", len(data))
            print(" -- Data:", bytePrint(data))
            print(self.__str__())
            print(" -- CRC check OK")

        return True
        
    def __sendAndRcv(self, data:bytearray, expected_length:int)->tuple:
        """ Odešle data, a přidá jim CRC, a vrátí tuple
            
            Returns:
                tuple: (data, crc_received, crc_ok,fn_code,addr) fn_code is second byte of response
        """
        # Create a bytearray for the request <1B addr>, <1B fn_r_in_reg>, <2B register>, <2B number of reg>, <2B CRC>
        # přečteme celý blok dat tj registry 0 - 9 (20 bajtů = 10x uint16)
        
        if debug:
            print("> Data to send:", bytePrint(data))
            print("> Data length:", len(data))
        crc = getCrc(data)
        data.append(crc[0])
        data.append(crc[1])
        if debug:
            print("> Data with CRC:", bytePrint(data))
            print("> Data length with CRC:", len(data))
        with serial.Serial(port, baudRate, timeout=timeOut) as ser:
            ser.write(data)
            if debug:
                print("> Data sent successfully")
                
            r= ser.read(expected_length)
            
            if debug:
                print("< Response received")
                print("< Response length:", len(r))
                print("< Response:", bytePrint(r))
                
            # pokud se nic nevrátilo nebo jsou data kratší jak 4 tak vracíme None
            if len(r) < 4:
                return (None, None, False, None, None)
                
            data=r[3:-2]
            crc_received = bytearray(r[-2:])
            crc_calculated = bytearray(getCrc(r[:-2]))
            
            if debug:
                print("< CRC received:", crc_received)
                print("< CRC calculated:", crc_calculated)
                print("< fn_code:", r[1])
            
            return (data, crc_received, crc_calculated == crc_received, r[1], r[0])
            
    def resetEnergy(self, addr:int=None)->bool:
        """Reset the energy of the meter.
        
        Args:
            addr (int, optional): The address of the meter. Defaults to None.
        
        Returns:
            bool: True if the reset was successful, False otherwise.
            
        """
        if addr is None:
            addr = addr_default
        
        # Create a bytearray for the request <1B addr>, <1B fn_reset_energy>, <2B CRC>
        request = bytearray([
            addr,
            fn_reset_energy,
        ])
    
        if debug:
            print(' -- Reset energy --')
        data, crc_received, crc_ok, fn_code,r_adr = self.__sendAndRcv(request, 4)
        if data is None:
            return False     
        return crc_ok and fn_code == fn_reset_energy and r_adr == addr

        
    def __str__(self):
        """Return a string representation of the masterData object.
        
        Returns:
            str: String representation of the masterData object.
            
        """
        return (f"Voltage: {self.voltage} V\n"
                f"Current: {self.current} A\n"
                f"Power: {self.power} W\n"
                f"Energy: {self.energy} Wh\n"
                f"Frequency: {self.frequency} Hz\n"
                f"Power factor: {self.pf}\n"
                f"Alarm: {self.alarm}")
        
    def setModBusAddr(self,newAddr:int,oldAddr:int=None)->bool:
        """Set the Modbus address of the meter
        
        Args:
            newAddr (int): The new Modbus address to set. Range is 0x01 to 0xF7.
            oldAddr (int, optional): The old Modbus address. Defaults to None.
        
        Returns:
            bool: True if the address was set successfully, False otherwise.
            
        """
        if newAddr < 0x01 or newAddr > 0xF7:
            raise ValueError("Address must be in the range 0x01 to 0xF7")
        
        oldAddr = oldAddr if oldAddr is not None else addr_default
        
        if newAddr == oldAddr:
            raise ValueError("New address must be different from old address")
        
        if newAddr == _general_addr:
            raise ValueError("New address cannot be the general address")
        
        rgAdr=2
        rq=bytearray([
            oldAddr,
            fn_w_reg,
            (rgAdr >> 8) & 0xFF,  # Register address high byte
            (rgAdr & 0xFF),  # Register address low byte
            (newAddr >> 8) & 0xFF,  # New address high byte
            (newAddr & 0xFF),  # New address low byte
        ])
        
        if debug:
            print(" -- Set Modbus address --")
            print("    newAddr:", newAddr)
        data, crc_received, crc_ok, fn_code, r_addr = self.__sendAndRcv(rq, 8)
        if data is None:
            return False
        return crc_ok and fn_code == fn_w_reg and r_addr == oldAddr
    
    def getModbusAddr(self, addr:int=addr_default)->int:
        """Get the Modbus address of the meter.
        
        Args:
            addr (int, optional): The address of the meter. Defaults to addr_default.  
                !! If we dont know the address, we can use None for general address !! but must be only one meter on the bus.
                Default adr use if None is passed.
        
        Returns:
            int: The Modbus address of the meter or None if the address could not be read.
            
        """
        if addr is None:
            addr = _general_addr
        rq=bytearray([
            addr,
            fn_r_hold_reg,
            0x00,  # Register address high byte
            0x02,  # Register address low byte
            0x00,  # Number of registers high byte
            0x01,  # Number of registers low byte
        ])
        
        if debug:
            print(" -- Get Modbus address --")
        data, crc_received, crc_ok, fn_code, r_addr = self.__sendAndRcv(rq, 7)
        if data is None:
            return None
        
        if crc_ok and fn_code == fn_r_hold_reg and r_addr == addr:
            return struct.unpack('>H', data[0:2])[0]
        
        return None
    
    def json(self)->dict:
        """Convert the masterData object to a JSON-like dictionary.
        
        Returns:
            dict: Dictionary representation of the masterData object.
            
        """
        return {
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "energy": self.energy,
            "frequency": self.frequency,
            "power_factor": self.pf,
            "alarm": self.alarm
        }
        
    def __repr__(self)->str:
        """Return a string representation of the masterData object for debugging.
        
        Returns:
            str: String representation of the masterData object.
            
        """
        return (f"masterData(voltage={self.voltage}, current={self.current}, power={self.power}, "
                f"energy={self.energy}, frequency={self.frequency}, power_factor={self.pf}, alarm={self.alarm})")

class registers:
    """Class for holding register addresses and lengths."""
    
    voltage = (0, 1)
    """Voltage register address and length."""
    
    current = (1, 2)
    """Current register address and length."""
    
    power = (3, 2)
    """Power register address and length."""
    
    energy = (5, 2)
    """Energy register address and length."""
    
    frequency = (7, 1)
    """Frequency register address and length."""
    
    power_factor = (8, 1)
    """Power factor register address and length."""
    
    alarm = (9, 1)
    """Alarm register address and length."""

