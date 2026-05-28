import socket
import struct
import json
import urllib.request
import urllib.error
import time
import argparse
from datetime import datetime, timezone

# --- Modbus source ---
XLINK_HOST = "157.253.200.226"
XLINK_PORT = 4196
MODBUS_TIMEOUT = 5.0

# --- Backend target ---
API_HOST = "172.24.100.46"
API_PORT = 8000
API_URL  = f"http://{API_HOST}:{API_PORT}/measurements"

STATION_ID = "uniandes-meteo-01"

CMD_LEER_METEO = b"\x01\x03\x00\x00\x00\x10\x44\x06"

SLOTS = [
    ("M1", "GHI",       "Wm2"),
    ("M2", "Rad.",      "Wm2"),
    ("M3", "Temp.",     "C"),
    ("M4", "Hum",       "%"),
    ("M5", "Pr. Aire",  "hPa"),
    ("M6", "Velocidad", "m/s"),
    ("M7", "Direcc.",   None),
    ("M8", "Precip.",   "mmh"),
]

EXPECTED_BYTE_COUNT = 32
EXPECTED_TOTAL      = 3 + EXPECTED_BYTE_COUNT + 2


def read_station() -> dict:
    with socket.create_connection((XLINK_HOST, XLINK_PORT), timeout=MODBUS_TIMEOUT) as sock:
        sock.sendall(CMD_LEER_METEO)
        raw = sock.recv(1024)

    if len(raw) < EXPECTED_TOTAL:
        raise ValueError(f"Respuesta corta: {len(raw)} bytes — raw: {raw.hex()}")

    func_code, byte_count = raw[1], raw[2]
    if func_code == 0x83:
        raise RuntimeError(f"Modbus exception: {raw[2]:#04x}")
    if func_code != 0x03:
        raise RuntimeError(f"Function code inesperado: {func_code:#04x}")
    if byte_count != EXPECTED_BYTE_COUNT:
        raise ValueError(f"Byte count inesperado: {byte_count}")

    floats = struct.unpack(">ffffffff", raw[3:35])

    now              = datetime.now(timezone.utc)
    ingested_at      = now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    sensor_timestamp = now.strftime("%Y/%m/%dT%H:%M:%S")

    return {
        "station_id":        STATION_ID,
        "ingested_at":       ingested_at,
        "measurement_count": len(SLOTS),
        "measurements": [
            {
                "slot":             slot,
                "label":            label,
                "value":            round(floats[i], 1),
                "unit":             unit,
                "sensor_timestamp": sensor_timestamp,
            }
            for i, (slot, label, unit) in enumerate(SLOTS)
        ],
    }


def post_measurements(payload: dict) -> int:
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def run_once(verbose: bool = True) -> bool:
    """Single read+post cycle. Returns True on full success."""
    try:
        payload = read_station()
        if verbose:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
    except (OSError, ValueError, RuntimeError) as e:
        print(f"❌ [{_now()}] Modbus error: {e}")
        return False

    try:
        status = post_measurements(payload)
        print(f"✅ [{_now()}] HTTP {status} — {payload['ingested_at']}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ [{_now()}] HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        print(f"❌ [{_now()}] No se pudo conectar a {API_URL}: {e.reason}")
    return False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="XLink → TimescaleDB ingestor")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously at --interval seconds (default: one-shot)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds when --loop is set (default: 60)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress full JSON payload output",
    )
    args = parser.parse_args()

    if not args.loop:
        run_once(verbose=not args.quiet)
        return

    print(f"▶ Loop mode: polling every {args.interval}s — Ctrl+C to stop")
    while True:
        cycle_start = time.monotonic()
        run_once(verbose=not args.quiet)
        elapsed = time.monotonic() - cycle_start
        sleep_for = max(0, args.interval - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()