"""
Serial Port Test Tool - throughput test + dial / incoming-call monitor
Brought to you by flykantech.com
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import os
import webbrowser

from utils import serial_utils
from utils import log_utils
from utils import throughput_utils
from utils import dial_utils
from utils import stability_utils


APP_NAME = "Serial Port Test Tool"
APP_VERSION = "2.0"
COMPANY = "Shenzhen VTOP Electronic Co., Ltd."
WEBSITE = "www.flykantech.com"
WEBSITE_URL = "https://www.flykantech.com"
SUPPORT_EMAIL = "dev@flykantech.com"
MAILTO_URL = f"mailto:{SUPPORT_EMAIL}"


class ComBusyApp:
    """Unified serial port test application."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {WEBSITE}")
        self.root.geometry("1050x700")

        # shared state
        self.ser = None
        self.dial_monitor = None
        self.log_buffer = log_utils.LogBuffer()
        self.testing = False
        self.conn_var = tk.StringVar(value="Disconnected")
        self.port_info_var = tk.StringVar(value="-")

        self._set_window_icon()
        self._create_notebook()
        self._create_statusbar()
        self._create_footer()
        self._update_conn_status()

    def _set_window_icon(self):
        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flykan.ico")
        if os.path.exists(ico):
            try:
                self.root.iconbitmap(ico)
            except Exception:
                pass

    def _open_website(self, _event=None):
        webbrowser.open(WEBSITE_URL)

    def _open_mail(self, _event=None):
        webbrowser.open(MAILTO_URL)

    # ─────────────────── serial port connection ───────────────────

    def _open_port(self):
        """Open the selected serial port (shared by all test tabs)."""
        port = self._get_selected_port()
        if not port:
            messagebox.showerror("Error", "Please select a serial port first.")
            return False
        baud = self._get_selected_baud()
        try:
            self.ser = serial_utils.open_serial(port, baud)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open serial port: {e}")
            return False
        self._global_log(f"[SYSTEM] Port {port} opened at {baud} bps.")
        self._update_conn_status()
        return True

    def _close_port(self):
        """Close the shared serial port."""
        serial_utils.close_serial(self.ser)
        self.ser = None
        self._global_log("[SYSTEM] Serial port closed.")
        self._update_conn_status()

    def _update_conn_status(self):
        connected = bool(self.ser and self.ser.is_open)
        self.conn_var.set("Connected" if connected else "Disconnected")
        self.conn_label.config(foreground="green" if connected else "red")
        self.open_btn.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.close_btn.config(state=tk.NORMAL if connected else tk.DISABLED)

    def _update_port_info(self, _event=None):
        port = self._get_selected_port()
        baud = self._get_selected_baud()
        self.port_info_var.set(f"{port or '-'} @ {baud} bps")

    # ─────────────────── tabs ───────────────────

    def _create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="Port Settings")
        self._build_settings_tab()

        self.tab_throughput = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_throughput, text="Throughput Test")
        self._build_throughput_tab()

        self.tab_dial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dial, text="Dial Test")
        self._build_dial_tab()

        self.tab_stability = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stability, text="Stability Test")
        self._build_stability_tab()

    # ─────────────────── status bar ───────────────────

    def _create_statusbar(self):
        bar = ttk.Frame(self.root, relief='sunken')
        bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 2))

        ttk.Label(bar, text="Connection:").pack(side=tk.LEFT, padx=(5, 0))
        self.conn_label = ttk.Label(bar, textvariable=self.conn_var, foreground="red")
        self.conn_label.pack(side=tk.LEFT, padx=(2, 20))

        ttk.Label(bar, text="Port:").pack(side=tk.LEFT)
        ttk.Label(bar, textvariable=self.port_info_var).pack(side=tk.LEFT, padx=(2, 0))

        brand = tk.Label(bar, text=WEBSITE, fg="blue", cursor="hand2",
                         font=("", 9, "underline"))
        brand.pack(side=tk.RIGHT, padx=5)
        brand.bind("<Button-1>", self._open_website)

    # ─────────────────── footer ───────────────────

    def _create_footer(self):
        footer = ttk.Frame(self.root)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(5, 10))

        ttk.Label(footer,
                  text=f"{APP_NAME} v{APP_VERSION}  |  (c) {COMPANY}. All rights reserved."
                  ).pack(side=tk.LEFT)

        ttk.Button(footer, text="About", command=self._show_about).pack(side=tk.RIGHT)

        mail = tk.Label(footer, text=SUPPORT_EMAIL, fg="blue", cursor="hand2",
                        font=("", 9, "underline"))
        mail.pack(side=tk.RIGHT, padx=10)
        mail.bind("<Button-1>", self._open_mail)

        link = tk.Label(footer, text=WEBSITE, fg="blue", cursor="hand2",
                        font=("", 9, "underline"))
        link.pack(side=tk.RIGHT, padx=10)
        link.bind("<Button-1>", self._open_website)

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_NAME} v{APP_VERSION}\n"
            f"{COMPANY}\n"
            f"{WEBSITE_URL}\n"
            f"Support: {SUPPORT_EMAIL}"
        )

    # ═══════════════ Port Settings ═══════════════

    def _build_settings_tab(self):
        frame = ttk.LabelFrame(self.tab_settings, text="Serial Port Configuration")
        frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_combo = ttk.Combobox(frame, state="readonly", width=30)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="Baud rate:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.baud_combo = ttk.Combobox(
            frame, state="readonly",
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.baud_combo.current(4)
        self.baud_combo.grid(row=1, column=1, padx=5, pady=5)

        self.port_combo.bind("<<ComboboxSelected>>", self._update_port_info)
        self.baud_combo.bind("<<ComboboxSelected>>", self._update_port_info)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=8)
        self.open_btn = ttk.Button(btn_frame, text="Open Port", command=self._open_port)
        self.open_btn.pack(side=tk.LEFT, padx=5)
        self.close_btn = ttk.Button(btn_frame, text="Close Port", command=self._close_port,
                                    state=tk.DISABLED)
        self.close_btn.pack(side=tk.LEFT, padx=5)

        self._refresh_ports()
        self._update_port_info()

        # global log area
        log_frame = ttk.LabelFrame(self.tab_settings, text="Global Log")
        log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Button(log_btn_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)
        ttk.Button(log_btn_frame, text="Export Log", command=self._export_log).pack(side=tk.LEFT, padx=5)

        self.log_text = tk.Text(log_frame, height=12, state='disabled')
        self.log_text.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

    def _refresh_ports(self):
        ports = serial_utils.list_serial_ports()
        self.port_combo['values'] = [f"{d} - {n}" for d, n in ports]
        if ports:
            self.port_combo.current(0)

    def _get_selected_port(self):
        val = self.port_combo.get()
        if not val:
            return ""
        return val.split(' ')[0]

    def _get_selected_baud(self):
        return int(self.baud_combo.get())

    def _global_log(self, msg):
        self.log_buffer.append(msg)
        self.root.after(0, self._global_log_ui, msg)

    def _global_log_ui(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def _clear_log(self):
        self.log_buffer.clear()
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def _export_log(self):
        if self.log_buffer.is_empty():
            messagebox.showinfo("Info", "The log is empty, nothing to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        header = (f"{APP_NAME} v{APP_VERSION} ({WEBSITE}, {SUPPORT_EMAIL}) - Log - "
                  f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
        self.log_buffer.export_to_file(path, header=header)
        messagebox.showinfo("Success", f"Saved to {path}")

    # ═══════════════ Throughput Test ═══════════════

    def _build_throughput_tab(self):
        top = ttk.Frame(self.tab_throughput)
        top.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top, text="Duration per baud rate (s):").grid(row=0, column=0, sticky=tk.W)
        self.tp_duration_var = tk.StringVar(value="5")
        ttk.Entry(top, textvariable=self.tp_duration_var, width=8).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(top, text="Fixed payload size (bytes):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.tp_payload_var = tk.StringVar(value="100000")
        ttk.Entry(top, textvariable=self.tp_payload_var, width=12).grid(row=0, column=3, padx=5, sticky=tk.W)

        self.tp_btn = ttk.Button(top, text="Start Throughput Test", command=self._start_throughput)
        self.tp_btn.grid(row=0, column=4, padx=20)

        self.tp_export_btn = ttk.Button(top, text="Export Results", command=self._export_throughput, state=tk.DISABLED)
        self.tp_export_btn.grid(row=0, column=5, padx=5)

        columns = ("Port", "Baud Rate", "Bytes Sent", "Bytes Received", "Errors",
                   "Throughput (B/s)", "Elapsed (s)", "Payload (bytes)", "Send Time (s)")
        self.tp_tree = ttk.Treeview(self.tab_throughput, columns=columns, show="headings", height=14)
        for c in columns:
            self.tp_tree.heading(c, text=c)
            self.tp_tree.column(c, width=100, anchor=tk.CENTER)
        self.tp_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tp_results = []

    def _start_throughput(self):
        if self.testing:
            messagebox.showwarning("Warning", "A test is already running, please wait for it to finish.")
            return
        port = self._get_selected_port()
        if not port:
            messagebox.showerror("Error", "Please select a serial port in Port Settings.")
            return
        try:
            duration = int(self.tp_duration_var.get())
            payload_len = int(self.tp_payload_var.get())
            if duration <= 0 or payload_len <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Duration and payload size must be positive integers.")
            return

        self.tp_btn.config(state=tk.DISABLED)
        self.tp_export_btn.config(state=tk.DISABLED)
        self.tp_tree.delete(*self.tp_tree.get_children())
        self.tp_results.clear()
        self.testing = True

        threading.Thread(target=self._run_throughput_thread,
                         args=(port, duration, payload_len), daemon=True).start()

    def _run_throughput_thread(self, port, duration, payload_len):
        baudrates = [9600, 19200, 38400, 57600, 115200]
        self._global_log(f"[THROUGHPUT] Starting test on {port}, {duration} s per baud rate...")

        for result in throughput_utils.run_throughput_test(
                port, baudrates, duration, payload_len,
                log_callback=self._global_log):
            self.tp_results.append(result)
            row = (result["port"], result["baudrate"], result["send_bytes"],
                   result["recv_bytes"], result["errors"],
                   f"{result['throughput']:.2f}", f"{result['elapsed']:.2f}",
                   result["send_fixed_len"], f"{result['send_time']:.3f}")
            self.root.after(0, lambda r=row: self.tp_tree.insert("", tk.END, values=r))

        self._global_log("[THROUGHPUT] Test finished.")
        self.testing = False
        self.root.after(0, self._enable_tp_buttons)

    def _enable_tp_buttons(self):
        self.tp_btn.config(state=tk.NORMAL)
        self.tp_export_btn.config(state=tk.NORMAL)

    def _export_throughput(self):
        if not self.tp_results:
            messagebox.showinfo("Info", "There are no results to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"{'Port':<8} {'Baud':<8} {'Sent':<12} {'Received':<12} "
                    f"{'Errors':<8} {'Throughput(B/s)':<18} {'Elapsed(s)':<12} "
                    f"{'Payload':<12} {'SendTime(s)':<12}\n")
            for r in self.tp_results:
                f.write(f"{r['port']:<8} {r['baudrate']:<8} {r['send_bytes']:<12} "
                        f"{r['recv_bytes']:<12} {r['errors']:<8} "
                        f"{r['throughput']:<18.2f} {r['elapsed']:<12.2f} "
                        f"{r['send_fixed_len']:<12} {r['send_time']:<12.3f}\n")
        messagebox.showinfo("Success", f"Saved to {path}")

    # ═══════════════ Dial Test ═══════════════

    def _build_dial_tab(self):
        inc_frame = ttk.Frame(self.tab_dial)
        inc_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Label(inc_frame, text="Incoming number:").pack(side=tk.LEFT)
        self.incoming_var = tk.StringVar(value="No incoming call.")
        ttk.Label(inc_frame, textvariable=self.incoming_var, foreground="blue").pack(side=tk.LEFT, padx=5)

        dial_frame = ttk.LabelFrame(self.tab_dial, text="Dial")
        dial_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(dial_frame, text="Dial prefix:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        self.dial_prefix = ttk.Entry(dial_frame, width=8)
        self.dial_prefix.insert(0, "9,")
        self.dial_prefix.grid(row=0, column=1, padx=5)

        ttk.Label(dial_frame, text="Phone number:").grid(row=0, column=2, sticky=tk.E, padx=5)
        self.dial_number_entry = ttk.Entry(dial_frame, width=20)
        self.dial_number_entry.grid(row=0, column=3, padx=5)

        ttk.Button(dial_frame, text="Dial", command=self._do_dial).grid(row=0, column=4, padx=10)

        ctrl_frame = ttk.Frame(self.tab_dial)
        ctrl_frame.pack(pady=5)
        self.dial_start_btn = ttk.Button(ctrl_frame, text="Off-hook",
                                         command=self._start_dial_monitor)
        self.dial_start_btn.pack(side=tk.LEFT, padx=5)
        self.dial_stop_btn = ttk.Button(ctrl_frame, text="Hang up",
                                        command=self._stop_dial_monitor, state=tk.DISABLED)
        self.dial_stop_btn.pack(side=tk.LEFT, padx=5)

        sig_frame = ttk.LabelFrame(self.tab_dial, text="Signal Line Status")
        sig_frame.pack(padx=10, pady=5, fill=tk.X)

        self.signal_vars = {}
        signals = ["CTS", "RTS", "DSR", "DTR", "CD", "RI", "TXD", "RXD", "BREAK"]
        for i, sig in enumerate(signals):
            ttk.Label(sig_frame, text=f"{sig}:").grid(row=0, column=i * 2, sticky=tk.E, padx=2)
            var = tk.StringVar(value="N/A")
            self.signal_vars[sig] = var
            ttk.Label(sig_frame, textvariable=var, width=7, relief='sunken',
                      anchor=tk.CENTER).grid(row=0, column=i * 2 + 1, padx=2)

        dial_log_frame = ttk.LabelFrame(self.tab_dial, text="Dial Log")
        dial_log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.dial_log_text = tk.Text(dial_log_frame, height=10, state='disabled')
        self.dial_log_text.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

    def _dial_log(self, msg):
        self._global_log(f"[DIAL] {msg}")
        self.root.after(0, self._dial_log_ui, msg)

    def _dial_log_ui(self, msg):
        self.dial_log_text.config(state='normal')
        self.dial_log_text.insert(tk.END, msg + '\n')
        self.dial_log_text.see(tk.END)
        self.dial_log_text.config(state='disabled')

    def _start_dial_monitor(self):
        # reuse the port opened on the settings tab; open it if not connected yet
        if not (self.ser and self.ser.is_open):
            if not self._open_port():
                return

        self.dial_start_btn.config(state=tk.DISABLED)
        self.dial_stop_btn.config(state=tk.NORMAL)
        self._dial_log("[SYSTEM] Port opened, monitoring signal lines and caller ID.")

        self.dial_monitor = dial_utils.DialMonitor(
            self.ser,
            log_callback=self._dial_log,
            caller_id_callback=self._on_caller_id
        )
        self.dial_monitor.signal_callback = self._on_signal_update
        self.dial_monitor.start()

    def _stop_dial_monitor(self):
        if self.dial_monitor:
            self.dial_monitor.stop()
            self.dial_monitor = None

        self.dial_start_btn.config(state=tk.NORMAL)
        self.dial_stop_btn.config(state=tk.DISABLED)
        self._dial_log("[SYSTEM] Monitoring stopped.")

        for var in self.signal_vars.values():
            var.set("N/A")
        self.incoming_var.set("No incoming call.")

    def _do_dial(self):
        if not self.dial_monitor:
            self._dial_log("[ERROR] Please go off-hook first.")
            return
        prefix = self.dial_prefix.get().strip()
        number = self.dial_number_entry.get().strip()
        if not number:
            self._dial_log("[INFO] Please enter a phone number.")
            return
        self.dial_monitor.dial(prefix, number)

    def _on_caller_id(self, number):
        self.root.after(0, lambda: self.incoming_var.set(number))

    def _on_signal_update(self, states):
        self.signal_vars["CTS"].set("ACTIVE" if states["CTS"] else "IDLE")
        self.signal_vars["RTS"].set("ACTIVE" if states["RTS"] else "IDLE")
        self.signal_vars["DSR"].set("ACTIVE" if states["DSR"] else "IDLE")
        self.signal_vars["DTR"].set("ACTIVE" if states["DTR"] else "IDLE")
        self.signal_vars["CD"].set("ACTIVE" if states["CD"] else "IDLE")
        self.signal_vars["RI"].set("ACTIVE" if states["RI"] else "IDLE")
        self.signal_vars["TXD"].set("BUSY" if states["TXD"] else "IDLE")
        self.signal_vars["RXD"].set("BUSY" if states["RXD"] else "IDLE")
        self.signal_vars["BREAK"].set("BREAK" if states["BREAK"] else "NORMAL")

    # ═══════════════ Stability Test ═══════════════

    def _build_stability_tab(self):
        config_frame = ttk.LabelFrame(self.tab_stability, text="Test Configuration")
        config_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(config_frame, text="Total duration (s):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.st_duration_var = tk.StringVar(value="3600")
        ttk.Entry(config_frame, textvariable=self.st_duration_var, width=10).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(config_frame, text="(suggested: 3600 = 1 hour)").grid(row=0, column=2, sticky=tk.W, padx=5)

        self.st_btn = ttk.Button(config_frame, text="Start Stability Test", command=self._start_stability)
        self.st_btn.grid(row=0, column=3, padx=20)

        self.st_stop_btn = ttk.Button(config_frame, text="Stop Test", command=self._stop_stability, state=tk.DISABLED)
        self.st_stop_btn.grid(row=0, column=4, padx=5)

        # live status panel
        status_frame = ttk.LabelFrame(self.tab_stability, text="Live Status")
        status_frame.pack(padx=10, pady=5, fill=tk.X)

        self.st_progress = ttk.Progressbar(status_frame, length=500, mode='determinate')
        self.st_progress.pack(padx=10, pady=5, fill=tk.X)

        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.st_progress_label = tk.StringVar(value="0%")
        ttk.Label(info_frame, textvariable=self.st_progress_label).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(info_frame, text="Elapsed:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.st_elapsed_label = tk.StringVar(value="00:00:00")
        ttk.Label(info_frame, textvariable=self.st_elapsed_label).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(info_frame, text="Remaining:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.st_remaining_label = tk.StringVar(value="01:00:00")
        ttk.Label(info_frame, textvariable=self.st_remaining_label).grid(row=0, column=5, sticky=tk.W, padx=5)

        # statistics
        stat_frame = ttk.Frame(status_frame)
        stat_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(stat_frame, text="Total transfers:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.st_total_label = tk.StringVar(value="0")
        ttk.Label(stat_frame, textvariable=self.st_total_label, font=("", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(stat_frame, text="Succeeded:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.st_success_label = tk.StringVar(value="0")
        ttk.Label(stat_frame, textvariable=self.st_success_label, foreground="green", font=("", 10, "bold")).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(stat_frame, text="Success rate:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.st_rate_label = tk.StringVar(value="--")
        ttk.Label(stat_frame, textvariable=self.st_rate_label, foreground="blue", font=("", 10, "bold")).grid(row=0, column=5, sticky=tk.W, padx=5)

        # error statistics
        err_frame = ttk.LabelFrame(self.tab_stability, text="Error Statistics")
        err_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(err_frame, text="Total errors:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.st_error_label = tk.StringVar(value="0")
        ttk.Label(err_frame, textvariable=self.st_error_label, foreground="red", font=("", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(err_frame, text="CRC errors:").grid(row=0, column=2, sticky=tk.W, padx=(30, 5))
        self.st_crc_err_label = tk.StringVar(value="0")
        ttk.Label(err_frame, textvariable=self.st_crc_err_label).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(err_frame, text="Timeouts:").grid(row=0, column=4, sticky=tk.W, padx=(30, 5))
        self.st_timeout_err_label = tk.StringVar(value="0")
        ttk.Label(err_frame, textvariable=self.st_timeout_err_label).grid(row=0, column=5, sticky=tk.W, padx=5)

        # log area
        log_frame = ttk.LabelFrame(self.tab_stability, text="Stability Test Log")
        log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.st_log_text = tk.Text(log_frame, height=8, state='disabled')
        self.st_log_text.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        self._st_running = False
        self._st_stop_flag = False

    def _st_log(self, msg):
        self._global_log(f"[STABILITY] {msg}")
        self.root.after(0, self._st_log_ui, msg)

    def _st_log_ui(self, msg):
        self.st_log_text.config(state='normal')
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.st_log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.st_log_text.see(tk.END)
        self.st_log_text.config(state='disabled')

    def _start_stability(self):
        if self.testing or self._st_running:
            messagebox.showwarning("Warning", "A test is already running, please wait for it to finish.")
            return
        port = self._get_selected_port()
        if not port:
            messagebox.showerror("Error", "Please select a serial port in Port Settings.")
            return
        try:
            duration = int(self.st_duration_var.get())
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Duration must be a positive integer.")
            return

        baud = self._get_selected_baud()
        self._st_running = True
        self._st_stop_flag = False
        self.st_btn.config(state=tk.DISABLED)
        self.st_stop_btn.config(state=tk.NORMAL)

        self._st_log(f"Stability test started - port: {port}, baud rate: {baud}, duration: {duration} s")
        threading.Thread(target=self._run_stability_thread,
                         args=(port, baud, duration), daemon=True).start()

    def _stop_stability(self):
        self._st_stop_flag = True
        self._st_log("Stop requested by user...")

    def _run_stability_thread(self, port, baud, duration):
        for status in stability_utils.run_stability_test(
                port, baud, duration,
                log_callback=self._st_log):
            if self._st_stop_flag:
                self._st_log("Test stopped manually.")
                break
            self.root.after(0, self._update_stability_status, status)

        self._st_running = False
        self.root.after(0, self._enable_st_buttons)

    def _update_stability_status(self, status):
        self.st_progress['value'] = status["progress"]
        self.st_progress_label.set(f"{status['progress']:.1f}%")

        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(status["elapsed"]))
        remaining_str = time.strftime("%H:%M:%S", time.gmtime(status["remaining"]))
        self.st_elapsed_label.set(elapsed_str)
        self.st_remaining_label.set(remaining_str)

        self.st_total_label.set(str(status["total"]))
        self.st_success_label.set(str(status["success"]))
        self.st_error_label.set(str(status["error"]))
        self.st_crc_err_label.set(str(status["crc_err"]))
        self.st_timeout_err_label.set(str(status["timeout_err"]))

        if status["total"] > 0:
            rate = status["success"] / status["total"] * 100
            self.st_rate_label.set(f"{rate:.2f}%")
        else:
            self.st_rate_label.set("--")

        if status.get("aborted"):
            self._st_log(f"[ABORTED] {status.get('abort_reason', 'Unknown error')}")

    def _enable_st_buttons(self):
        self.st_btn.config(state=tk.NORMAL)
        self.st_stop_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    try:  # keep the UI crisp on high-DPI displays (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    app = ComBusyApp(root)
    root.mainloop()
