"""Dial and incoming-call monitoring core logic."""

import time
import threading
from . import serial_utils


class DialMonitor:
    """Dial and incoming-call monitor (runs in background threads)."""

    def __init__(self, ser, log_callback=None, caller_id_callback=None):
        self.ser = ser
        self.log_callback = log_callback or (lambda m: None)
        self.caller_id_callback = caller_id_callback or (lambda n: None)
        self.running = False
        self._tx_busy = False
        self._rx_busy = False
        self._lock = threading.Lock()

    @property
    def tx_busy(self):
        with self._lock:
            return self._tx_busy

    @property
    def rx_busy(self):
        with self._lock:
            return self._rx_busy

    def start(self):
        """Start the monitoring threads."""
        self.running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._signal_thread = threading.Thread(target=self._signal_loop, daemon=True)
        self._signal_thread.start()

    def stop(self):
        """Stop monitoring."""
        self.running = False

    def dial(self, prefix, number):
        """Perform dialing in the background."""
        if not self.ser or not self.ser.is_open:
            self.log_callback("[ERROR] Serial port not open.")
            return
        full_number = f"ATDT{prefix}{number}\r\n"
        self.log_callback(f"[DIAL] Sending: {full_number.strip()}")
        threading.Thread(target=self._dial_thread, args=(full_number,), daemon=True).start()

    def _dial_thread(self, full_number):
        try:
            with self._lock:
                self._tx_busy = True
            sent = self.ser.write(full_number.encode())
            if sent != len(full_number.encode()):
                self.log_callback(f"[WARN] Incomplete write: {sent}/{len(full_number.encode())} bytes")

            time.sleep(1)
            response = b""
            wait_start = time.time()
            while time.time() - wait_start < 3:
                if self.ser.in_waiting:
                    response += self.ser.read(self.ser.in_waiting)
                else:
                    time.sleep(0.1)
            if response:
                with self._lock:
                    self._rx_busy = True
                self.log_callback(f"[MODEM] Response: {response.decode(errors='ignore').strip()}")
        except Exception as e:
            self.log_callback(f"[ERROR] Dial failed: {e}")
        finally:
            with self._lock:
                self._tx_busy = False

    def _monitor_loop(self):
        buffer = b""
        last_ri = False
        try:
            while self.running and self.ser and self.ser.is_open:
                current_ri = self.ser.ri
                if current_ri and not last_ri:
                    self.log_callback("[RING] Incoming call detected!")
                last_ri = current_ri

                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    buffer += data
                    lines = buffer.split(b'\r\n')
                    buffer = lines[-1]
                    for line in lines[:-1]:
                        text_line = line.decode(errors='ignore').strip()
                        if text_line:
                            self.log_callback(f"[MODEM] {text_line}")
                        caller = serial_utils.parse_clip_line(text_line)
                        if caller:
                            self.caller_id_callback(caller)
                            self.log_callback(f"[CALLER ID] {caller}")
                time.sleep(0.1)
        except Exception as e:
            self.log_callback(f"[ERROR] Monitor error: {e}")

    def _signal_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                # report signal states back through the callback so the UI can update
                states = serial_utils.get_signal_states(self.ser)
                states["TXD"] = self.tx_busy
                states["RXD"] = self.rx_busy
                if hasattr(self, 'signal_callback') and self.signal_callback:
                    self.signal_callback(states)
                time.sleep(0.5)
            except Exception as e:
                self.log_callback(f"[ERROR] Signal read error: {e}")
                break
