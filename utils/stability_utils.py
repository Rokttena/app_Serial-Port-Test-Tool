"""Stability test core logic - CRC verified loopback test."""

import time
import datetime

try:  # prefer crcmod, fall back to the built-in equivalent when unavailable
    import crcmod
except ImportError:  # pragma: no cover - used when crcmod is not installed
    crcmod = None

from . import serial_utils


def _crc16_arc(data: bytes) -> int:
    """CRC-16/ARC (poly 0x8005 reflected to 0xA001, init 0x0000, input and output reflected).

    Produces exactly the same result as crcmod.predefined.Crc("crc-16").
    """
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def calculate_crc(data: str) -> str:
    """Calculate the CRC-16 check code."""
    if crcmod is not None:
        crc16 = crcmod.predefined.Crc("crc-16")
        crc16.update(data.encode("utf-8"))
        return hex(crc16.crcValue)[2:].zfill(4)
    return format(_crc16_arc(data.encode("utf-8")), "04x")


def run_stability_test(port_name, baudrate, test_duration, log_callback=None):
    """
    Run a stability test (CRC verified loopback) on the given serial port.

    Args:
        port_name: serial port device name
        baudrate: baud rate
        test_duration: total test duration in seconds
        log_callback: log callback (msg) -> None

    Yields:
        dict: live status with elapsed, remaining, progress, success, error,
              crc_err, timeout_err, total fields
    """
    ser = None
    success_count = 0
    error_count = 0
    crc_error_count = 0
    timeout_error_count = 0
    start_time = time.time()
    last_status_time = start_time
    update_interval = 1.0  # push live status once per second

    try:
        ser = serial_utils.open_serial(port_name, baudrate, timeout=1)
        if log_callback:
            log_callback(f"[TEST] Starting - port: {port_name}, baud rate: {baudrate}, "
                         f"duration: {test_duration} s")

        while time.time() - start_time < test_duration:
            current_time = time.time()

            # build a uniquely identifiable test payload
            total_count = success_count + error_count
            raw_data = f"TEST_TS_{datetime.datetime.now().strftime('%f')}_CNT_{total_count}"
            crc_code = calculate_crc(raw_data)
            send_data = f"{raw_data}|{crc_code}"

            # send data
            ser.write((send_data + "\n").encode("utf-8"))

            # receive data (wait for a newline, at most 1 second)
            received_data = b""
            read_start = time.time()
            while b"\n" not in received_data and time.time() - read_start < 1:
                if ser.in_waiting:
                    received_data += ser.read(ser.in_waiting)
                time.sleep(0.01)

            # verify received data
            if not received_data:
                timeout_error_count += 1
                error_count += 1
                if log_callback:
                    log_callback(f"[ERROR] Timeout - no data received (sent: {raw_data})")
            else:
                received_str = received_data.decode("utf-8").strip()
                if "|" not in received_str:
                    error_count += 1
                    if log_callback:
                        log_callback(f"[ERROR] Malformed data - received: {received_str}")
                else:
                    recv_raw, recv_crc = received_str.split("|", 1)
                    calculated_crc = calculate_crc(recv_raw)

                    if calculated_crc != recv_crc:
                        crc_error_count += 1
                        error_count += 1
                        if log_callback:
                            log_callback(f"[ERROR] CRC mismatch - received: {recv_crc}, calculated: {calculated_crc}")
                    elif recv_raw != raw_data:
                        error_count += 1
                        if log_callback:
                            log_callback(f"[ERROR] Data mismatch - sent: {raw_data}, received: {recv_raw}")
                    else:
                        success_count += 1

            # push live status at the configured interval
            if current_time - last_status_time >= update_interval:
                elapsed = current_time - start_time
                remaining = max(0, test_duration - elapsed)
                yield {
                    "elapsed": elapsed,
                    "remaining": remaining,
                    "progress": (elapsed / test_duration) * 100 if test_duration > 0 else 0,
                    "success": success_count,
                    "error": error_count,
                    "crc_err": crc_error_count,
                    "timeout_err": timeout_error_count,
                    "total": success_count + error_count,
                    "finished": False,
                }
                last_status_time = current_time

            time.sleep(0.01)

        # test finished
        elapsed = time.time() - start_time
        yield {
            "elapsed": elapsed,
            "remaining": 0,
            "progress": 100,
            "success": success_count,
            "error": error_count,
            "crc_err": crc_error_count,
            "timeout_err": timeout_error_count,
            "total": success_count + error_count,
            "finished": True,
        }
        if log_callback:
            total = success_count + error_count
            rate = (success_count / total * 100) if total > 0 else 0
            log_callback(f"[TEST] Finished! Total transfers: {total}, succeeded: {success_count}, "
                         f"errors: {error_count}, success rate: {rate:.2f}%")

    except Exception as e:
        elapsed = time.time() - start_time
        yield {
            "elapsed": elapsed,
            "remaining": 0,
            "progress": 0,
            "success": success_count,
            "error": error_count,
            "crc_err": crc_error_count,
            "timeout_err": timeout_error_count,
            "total": success_count + error_count,
            "finished": True,
            "aborted": True,
            "abort_reason": str(e),
        }
        if log_callback:
            log_callback(f"[ERROR] Stability test exception: {e}")
    finally:
        serial_utils.close_serial(ser)
        if log_callback:
            log_callback("[TEST] Serial port closed")
