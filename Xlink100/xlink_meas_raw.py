import socket
import time


XLINK_HOST = "192.168.88.1"
XLINK_PORT = 3001
INTERVALO = 3.0


def leer_respuesta(sock, segundos=2.0):
    buf = bytearray()
    sock.settimeout(0.3)
    deadline = time.monotonic() + segundos
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            deadline = time.monotonic() + 0.5
        except socket.timeout:
            if buf:
                break
    return buf.decode("ascii", errors="replace")


def main():
    sock = socket.create_connection((XLINK_HOST, XLINK_PORT), timeout=5.0)
    print(f"Conectado a {XLINK_HOST}:{XLINK_PORT}")

    leer_respuesta(sock, segundos=1.0)

    try:
        while True:
            print(f"\n========== {time.strftime('%H:%M:%S')} ==========")
            sock.sendall(b"MEAS LAST\r\n")
            respuesta = leer_respuesta(sock, segundos=2.0)
            print(respuesta)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\nDetenido por usuario")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
