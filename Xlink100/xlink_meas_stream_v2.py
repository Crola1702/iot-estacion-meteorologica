import socket
import time


XLINK_HOST = "192.168.88.1"
XLINK_PORT = 3001
INTERVALO = 15.0
TIEMPO_LECTURA = 12.0


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


def main():
    sock = socket.create_connection((XLINK_HOST, XLINK_PORT), timeout=5.0)
    print(f"Conectado a {XLINK_HOST}:{XLINK_PORT}")

    banner = leer_todo(sock, segundos=2.0)
    print(f"Banner: {banner!r}")

    try:
        while True:
            print(f"\n{'=' * 60}")
            print(f"  Solicitud: {time.strftime('%H:%M:%S')}")
            print(f"{'=' * 60}")
            sock.sendall(b"MEAS LAST\r\n")
            respuesta = leer_todo(sock, segundos=TIEMPO_LECTURA)
            print(respuesta)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\nDetenido por usuario")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
