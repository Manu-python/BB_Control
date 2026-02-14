import serial.tools.list_ports


def get_available_ports():
    """
    Returns list of available serial ports.
    """
    return list(serial.tools.list_ports.comports())
