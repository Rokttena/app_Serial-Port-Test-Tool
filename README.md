# Serial Port Test Tool

**A free Windows serial port test tool for USB / RS-232 / UART devices — measure throughput, run CRC-verified stability (soak) tests, and dial / monitor calls over AT commands, all in one Python Tkinter GUI.**

Brought to you by [flykantech.com](https://www.flykantech.com) · Shenzhen VTOP Electronic Co., Ltd.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![pyserial](https://img.shields.io/badge/pyserial-%3E%3D3.5-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green)

> Serial port tester · RS-232 test software · USB-to-serial throughput benchmark · baud rate test ·
> loopback test · CRC16 verification · AT command tool · modem / caller-ID monitor

---

## What it does

One executable-style Python app with four tabs, sharing a single open COM port:

| Tab | Purpose |
| --- | --- |
| **Port Settings** | Enumerate COM ports, pick baud rate (9600 – 115200), open/close port, live global log with export |
| **Throughput Test** | Send a fixed payload at each baud rate and report bytes sent/received, errors, elapsed time and throughput (B/s) |
| **Dial Test** | Off-hook, dial with `ATDT` (prefix + number), parse caller ID (`+CLIP`), watch live modem lines (CTS/RTS/DSR/DTR/CD/RI/TXD/RXD/BREAK) |
| **Stability Test** | Long-running (hours) CRC-verified loopback soak test with CRC errors, timeouts and success-rate statistics |

### Key features

- **Automatic COM port detection** — refreshable port list with device description, no manual device-manager digging.
- **Baud rate benchmark** — sweeps 9600 / 19200 / 38400 / 57600 / 115200 bps, configurable per-rate duration (default 5 s) and payload size (default 100 000 bytes).
- **CRC-verified stability testing** — every frame `TEST_TS_<us>_CNT_<n>|<crc>` is verified on return using CRC-16/ARC (`crcmod` used when installed, otherwise a built-in drop-in implementation). Distinguishes **CRC mismatch**, **data mismatch**, **malformed frame** and **timeout**, up to multi-hour runs (default 3600 s).
- **AT command dialing** — send `ATDT<prefix><number>` (e.g. prefix `9,`) and read the modem response.
- **Incoming call / caller ID monitor** — detects the RI ring line and parses `+CLIP` caller-ID numbers in the background.
- **Live signal line status** — 9 modem control lines refreshed every 500 ms.
- **Exportable reports** — throughput tables and full session logs save to `.txt` for QA records.
- **Non-blocking UI** — all tests run in worker threads; the GUI stays responsive, with progress bar, elapsed/remaining time and live counters.

---

## Quick start

```bash
# 1. clone
git clone https://github.com/Rokttena/app_Serial-Port-Test-Tool.git
cd app_Serial-Port-Test-Tool

# 2. install the only hard dependency
pip install -r requirements.txt

# 3. run
python main.py
```

## Requirements

- Python 3.8 or newer (uses only the standard library for the GUI: `tkinter`)
- [`pyserial`](https://pypi.org/project/pyserial/) >= 3.5 — required
- [`crcmod`](https://pypi.org/project/crcmod/) >= 1.7 — optional; falls back to a built-in CRC-16/ARC routine
- A free serial port (USB-to-serial adapter, RS-232 port, or modem)

```txt
pyserial>=3.5
crcmod>=1.7
```

## Typical wiring for loopback tests

Short **TX → RX** (and GND ↔ GND) on the same port, or connect two ports of the same adapter
cross-wise (TX1→RX2, RX1←TX2). Throughput and stability tabs expect the data sent to come back.

---

## Usage

1. **Port Settings** — click *Refresh*, select your port, choose the baud rate, press **Open Port**.
   Status bar turns green when connected.
2. **Throughput Test** — set duration per baud rate and payload size, press **Start Throughput Test**,
   then **Export Results** for a tabulated report.
3. **Stability Test** — set total duration in seconds (3600 = 1 hour), press **Start Stability Test**.
   Watch total transfers, successes, success rate, CRC errors and timeouts; stop anytime.
4. **Dial Test** — press **Off-hook** to start monitoring, enter prefix and phone number, press **Dial**.
   Incoming numbers appear at the top; press **Hang up** to stop monitoring.
5. Any tab: **Export Log** in *Port Settings* dumps the whole session to a text file.

## Project layout

```text
main.py                  # Tkinter application shell: tabs, status bar, threading glue
utils/serial_utils.py    # port enumeration, open/close, AT helpers, +CLIP parsing, line states
utils/throughput_utils.py# multi-baud throughput benchmark
utils/stability_utils.py # CRC-16/ARC verified loopback soak test
utils/dial_utils.py      # background dial + ring/caller-ID monitor
utils/log_utils.py       # thread-safe log buffer with file export
```

## FAQ

**No ports listed?** Install the USB-to-serial driver (FTDI / CH340 / CP210x / Prolific) and press *Refresh*.

**"Unable to open serial port"?** The port is already in use — close other terminal software (PuTTY,
Arduino Serial Monitor, vendor tools) and retry.

**Stability test reports 100 % timeouts?** TX/RX are not looped back, or the remote side does not echo
the frame. Check wiring and that both ends use the same baud rate.

**Can it run on Linux/macOS?** Yes — the app is pure Python + `tkinter`; port names simply show up as
`/dev/ttyUSB*`, `/dev/ttyACM*` or `/dev/cu.*`.

---

## Support & company

Issues and feature requests: [GitHub Issues](https://github.com/Rokttena/app_Serial-Port-Test-Tool/issues)
· Email: dev@flykantech.com · Web: [www.flykantech.com](https://www.flykantech.com)

© Shenzhen VTOP Electronic Co., Ltd. All rights reserved.
