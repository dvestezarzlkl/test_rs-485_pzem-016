

def bytePrint(data:bytearray)->str:
    """Convert bytearray to hex string representation
    
    Args:
        data (bytearray): Data to convert.
        
    Returns:
        str: Hex string representation of the data.
    """
    
    if not isinstance(data, bytearray):
        data=bytearray(data)
    return ' '.join(format(x, '02x') for x in data)

def getCrc(data:bytearray)->tuple:
    """Calculate CRC16 for Modbus RTU
    
    Returns:
        tuple: CRC16 as a tuple of two bytes (low byte, high byte).

    """
    crc = 0xFFFF
    for pos in range(0, len(data)):
        crc ^= data[pos]
        for i in range(0, 8):
            if (crc & 0x0001) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return (crc & 0xFF, (crc >> 8) & 0xFF)