"""Throughput test core logic."""

import time
from . import serial_utils


def run_throughput_test(port_name, baudrates, test_duration, custom_test_len, log_callback=None):
    """
    Run a multi-baud-rate throughput test on the given serial port.

    Args:
        port_name: serial port device name
        baudrates: list of baud rates, e.g. [9600, 115200]
        test_duration: test duration in seconds for each baud rate
        custom_test_len: payload size in bytes for the fixed-length send test
        log_callback: log callback (msg) -> None

    Yields:
        dict: test result for each baud rate
    """
    test_packet = b'0123456789ABCDEF' * 4  # 64 bytes per packet

    for baudrate in baudrates:
        ser = None
        try:
            ser = serial_utils.open_serial(port_name, baudrate, timeout=0.1)
        except Exception as e:
            if log_callback:
                log_callback(f"[ERROR] Failed to open {port_name} @ {baudrate}: {e}")
            continue

        send_bytes = 0
        recv_bytes = 0
        errors = 0
        start_time = time.time()

        # Phase 1: continuous send/receive
        try:
            while time.time() - start_time < test_duration:
                try:
                    sent = ser.write(test_packet)
                    send_bytes += sent
                except Exception as ex:
                    errors += 1
                    if log_callback:
                        log_callback(f"[WARN] Write error: {ex}")

                try:
                    data = ser.read(ser.in_waiting or 1)
                    recv_bytes += len(data)
                except Exception as ex:
                    errors += 1
                    if log_callback:
                        log_callback(f"[WARN] Read error: {ex}")
        except Exception as ex:
            if log_callback:
                log_callback(f"[ERROR] Throughput test error: {ex}")

        # Phase 2: fixed-length payload send timing
        packets_needed = custom_test_len // len(test_packet)
        remainder = custom_test_len % len(test_packet)
        send_fixed_len = packets_needed * len(test_packet) + remainder

        send_start = time.time()
        try:
            full_payload = test_packet * packets_needed
            if remainder > 0:
                full_payload += b'0' * remainder
            ser.write(full_payload)
        except Exception as ex:
            errors += 1
            if log_callback:
                log_callback(f"[WARN] Fixed-length send error: {ex}")
        send_end = time.time()
        send_time = send_end - send_start

        serial_utils.close_serial(ser)

        elapsed = time.time() - start_time
        throughput = recv_bytes / elapsed if elapsed > 0 else 0

        result = {
            "port": port_name,
            "baudrate": baudrate,
            "send_bytes": send_bytes,
            "recv_bytes": recv_bytes,
            "errors": errors,
            "throughput": throughput,
            "elapsed": elapsed,
            "send_fixed_len": send_fixed_len,
            "send_time": send_time,
        }
        yield result
