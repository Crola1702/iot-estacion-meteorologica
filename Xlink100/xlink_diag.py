import socket
import time


XLINK_HOST = "192.168.88.1"
XLINK_PORT = 3001


def leer_todo(sock, segundos=3.0):
    buf = bytearray()
    sock.settimeout(0.3)
    deadline = time.monotonic() + segundos
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            deadline = time.monotonic() + 0.8
        except socket.timeout:
            if buf:
                continue
    return bytes(buf)


def mostrar(etiqueta, datos):
    print(f"\n--- {etiqueta} ---")
    print(f"Bytes recibidos: {len(datos)}")
    if datos:
        print(f"Hex: {datos[:200].hex()}")
        print(f"Texto: {datos.decode('ascii', errors='replace')!r}")
    else:
        print("(sin respuesta)")


def main():
    print(f"Conectando a {XLINK_HOST}:{XLINK_PORT}...")
    sock = socket.create_connection((XLINK_HOST, XLINK_PORT), timeout=5.0)
    print("Conectado.")

    banner = leer_todo(sock, segundos=2.0)
    mostrar("BANNER INICIAL", banner)

    comandos = [
        b"\r\n",
        b"VER\r\n",
        b"ver\r\n",
        b"STATUS\r\n",
        b"HELP\r\n",
        b"?\r\n",
        b"MEAS LAST\r\n",
        b"MEAS\r\n",
        b"M1 LAST\r\n",
        b"TIME\r\n",
    ]

    for cmd in comandos:
        print(f"\n>>> Enviando: {cmd!r}")
        sock.sendall(cmd)
        resp = leer_todo(sock, segundos=2.5)
        mostrar(f"Respuesta a {cmd!r}", resp)
        time.sleep(0.5)

    sock.close()
    print("\nConexión cerrada.")


if __name__ == "__main__":
    main()
