import socket
import time
import json
import re
from datetime import datetime


XLINK_HOST = "192.168.88.1"
XLINK_PORT = 3001
INTERVALO = 60.0
TIEMPO_LECTURA = 12.0

STATION_ID = "uniandes-meteo-01"

UNIDADES_CORREGIDAS = {
    "atm": "hPa",
}


def leer_todo(sock, segundos):
    buf = bytearray()
    sock.settimeout(0.5)
    deadline = time.monotonic() + segundos
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            deadline = time.monotonic() + 2.0
        except socket.timeout:
            continue
    return buf.decode("ascii", errors="replace")


def parse_meas_last(texto):
    mediciones = []
    patron = re.compile(
        r"Measurement\s+(M\d+)\s+(.+?)\s+reading\s*\r?\n"
        r"\s*([-+]?\d+\.?\d*)\s*(\S*)\s*\r?\n"
        r"\s*(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})",
        re.MULTILINE,
    )

    for match in patron.finditer(texto):
        slot, etiqueta, valor, unidad, fecha, hora = match.groups()
        unidad_limpia = UNIDADES_CORREGIDAS.get(unidad, unidad) if unidad else None

        mediciones.append({
            "slot": slot,
            "label": etiqueta.strip(),
            "value": float(valor),
            "unit": unidad_limpia,
            "sensor_timestamp": f"{fecha}T{hora.replace('/', '-')}",
        })

    return mediciones


def construir_payload(mediciones):
    return {
        "station_id": STATION_ID,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        "measurement_count": len(mediciones),
        "measurements": mediciones,
    }


def enviar_simulado(payload):
    print(f"\n[SEND -> https://ingest.tu-server.com/v1/datalogger/{STATION_ID}]")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"[OK] {payload['measurement_count']} mediciones enviadas")


def main():
    sock = socket.create_connection((XLINK_HOST, XLINK_PORT), timeout=5.0)
    print(f"Conectado a {XLINK_HOST}:{XLINK_PORT}")

    leer_todo(sock, segundos=2.0)
    print(f"Iniciando muestreo cada {INTERVALO:.0f}s\n")

    try:
        while True:
            t_inicio = time.monotonic()
            print(f"--- Solicitud {time.strftime('%H:%M:%S')} ---")

            sock.sendall(b"MEAS LAST\r\n")
            respuesta = leer_todo(sock, segundos=TIEMPO_LECTURA)

            mediciones = parse_meas_last(respuesta)

            if not mediciones:
                print("Sin mediciones parseadas. Respuesta cruda:")
                print(respuesta)
            else:
                payload = construir_payload(mediciones)
                enviar_simulado(payload)

            transcurrido = time.monotonic() - t_inicio
            sleep_restante = max(0, INTERVALO - transcurrido)
            print(f"\nProxima solicitud en {sleep_restante:.1f}s...")
            time.sleep(sleep_restante)

    except KeyboardInterrupt:
        print("\nDetenido por usuario")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
