import socket
import time
from contextlib import contextmanager


class XLinkCLI:
    def __init__(self, host, port=3001, timeout=5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        self._drain_banner()

    def close(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.sock.close()
            self.sock = None

    def _drain_banner(self):
        self.sock.settimeout(1.0)
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
        except socket.timeout:
            pass
        finally:
            self.sock.settimeout(self.timeout)

    def send(self, cmd, read_seconds=2.0):
        if not self.sock:
            raise RuntimeError("Socket no conectado")
        payload = (cmd.strip() + "\r\n").encode("ascii")
        self.sock.sendall(payload)
        return self._read_response(read_seconds)

    def _read_response(self, read_seconds):
        buf = bytearray()
        deadline = time.monotonic() + read_seconds
        self.sock.settimeout(0.3)
        try:
            while time.monotonic() < deadline:
                try:
                    chunk = self.sock.recv(4096)
                except socket.timeout:
                    if buf and (b">" in buf or buf.endswith(b"\r\n")):
                        break
                    continue
                if not chunk:
                    break
                buf.extend(chunk)
                deadline = time.monotonic() + 0.5
        finally:
            self.sock.settimeout(self.timeout)
        return buf.decode("ascii", errors="replace")


@contextmanager
def open_xlink(host, port=3001):
    cli = XLinkCLI(host, port=port)
    cli.connect()
    try:
        yield cli
    finally:
        cli.close()


def parse_meas_last(respuesta):
    mediciones = {}
    for linea in respuesta.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith(">"):
            continue
        partes = linea.split(",")
        if len(partes) >= 4:
            etiqueta = partes[2].strip()
            try:
                valor = float(partes[3].strip())
            except ValueError:
                continue
            mediciones[etiqueta] = {
                "fecha": partes[0].strip(),
                "hora": partes[1].strip(),
                "valor": valor,
                "unidades": partes[4].strip() if len(partes) > 4 else "",
            }
    return mediciones


def stream_polling(host, port, intervalo_segundos=5.0, callback=None):
    with open_xlink(host, port) as xl:
        while True:
            inicio = time.monotonic()
            try:
                respuesta = xl.send("MEAS LAST", read_seconds=3.0)
                mediciones = parse_meas_last(respuesta)

                if callback:
                    callback(mediciones)
                else:
                    print(f"--- {time.strftime('%H:%M:%S')} ---")
                    for etiqueta, datos in mediciones.items():
                        print(f"  {etiqueta}: {datos['valor']} {datos['unidades']}")
            except (socket.timeout, OSError) as e:
                print(f"Error de socket: {e} — reintentando")
                xl.close()
                time.sleep(2.0)
                xl.connect()
                continue

            transcurrido = time.monotonic() - inicio
            sleep_restante = max(0, intervalo_segundos - transcurrido)
            time.sleep(sleep_restante)


def publicar_mqtt(mediciones):
    pass


if __name__ == "__main__":
    XLINK_HOST = "192.168.88.1"
    XLINK_PORT = 3001

    stream_polling(XLINK_HOST, XLINK_PORT, intervalo_segundos=5.0)
