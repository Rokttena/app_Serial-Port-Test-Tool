"""Serial port helpers: port scanning, open/close, AT command exchange."""

import serial
import serial.tools.list_ports
import time
import re


def list_serial_ports():
    """Return the available serial ports as a list of (device, description)."""
    ports = serial.tools.list_ports.comports()
    return [(p.device, p.description) for p in ports]


def open_serial(port, baudrate=115200, timeout=1):
    """Open the serial port and return the Serial object."""
    return serial.Serial(port, baudrate=baudrate, timeout=timeout)


def close_serial(ser):
    """Close the serial port safely."""
    if ser and ser.is_open:
        try:
            ser.close()
        except Exception:
            pass


def send_at_command(ser, cmd, wait=0.5):
    """Send an AT command and read the response."""
    ser.write((cmd + "\r\n").encode())
    time.sleep(wait)
    resp = ser.read_all().decode(errors='ignore')
    return resp.strip()


def send_at_wait_ok(ser, cmd, timeout=5.0):
    """Send an AT command and wait for an OK/ERROR response."""
    ser.write((cmd + "\r\n").encode())
    start = time.time()
    buffer = ""
    while time.time() - start < timeout:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode(errors='ignore')
            buffer += data
            if "OK" in buffer or "ERROR" in buffer:
                break
        time.sleep(0.1)
    return buffer.strip()


def parse_clip_line(text_line):
    """Parse the caller number from a +CLIP: line."""
    if text_line.startswith("+CLIP:"):
        m = re.search(r'\"(.+?)\"', text_line)
        if m:
            return m.group(1)
    return None


def get_signal_states(ser):
    """Return the current signal line states as a dict."""
    return {
        "CTS": ser.cts,
        "RTS": ser.rts,
        "DSR": ser.dsr,
        "DTR": ser.dtr,
        "CD": ser.cd,
        "RI": ser.ri,
        "BREAK": ser.break_condition,
    }
