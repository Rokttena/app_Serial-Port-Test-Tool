"""Log helpers: thread-safe log buffer and export."""

import threading
import time


class LogBuffer:
    """Thread-safe log buffer."""

    def __init__(self):
        self._lines = []
        self._lock = threading.Lock()

    def append(self, line):
        with self._lock:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            self._lines.append(f"[{timestamp}] {line}")

    def clear(self):
        with self._lock:
            self._lines.clear()

    def get_all(self):
        with self._lock:
            return list(self._lines)

    def is_empty(self):
        with self._lock:
            return len(self._lines) == 0

    def export_to_file(self, file_path, header=None):
        """Export the buffered log to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            if header:
                f.write(header + '\n')
            with self._lock:
                for line in self._lines:
                    f.write(line + '\n')
