#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import websocket
import requests
import json
import ssl
import time
import termios
import tty
import sys
import warnings
import base64
import threading
import os
from urllib3.exceptions import NotOpenSSLWarning

warnings.filterwarnings("ignore", category=NotOpenSSLWarning)


class SamsungTVController:
    def __init__(self, tv_ip, device_name="Terminal", token=None):
        self.tv_ip = tv_ip
        self.token_file = f".tv_token_{tv_ip.replace('.', '_')}"
        self.token = token or self._load_token() or self._generate_token()
        self.device_name = base64.b64encode(device_name.encode()).decode()
        self.ws_url = f"wss://{tv_ip}:8002/api/v2/channels/samsung.remote.control?name={self.device_name}&token={self.token}"
        self.websocket = None
        self.is_ready = False

        self.app_list = {
            "netflix": "3201907018807", "youtube": "111299001912",
            "disney": "3201901017640", "globoplay": "3201807016597",
            "spotify": "3201606009684", "appletv": "3201910019365",
            "browser": "org.tizen.browser", "stremio": "3202306031311"
        }

        self.key_mapping = {
            **{str(i): f"KEY_{i}" for i in range(10)},
            "UP": "KEY_UP", "DOWN": "KEY_DOWN", "LEFT": "KEY_LEFT", "RIGHT": "KEY_RIGHT",
            "ENTER": "KEY_ENTER", "RETURN": "KEY_RETURN", "EXIT": "KEY_RETURN",
            "MENU": "KEY_MENU", "HOME": "KEY_HOME", "GUIDE": "KEY_GUIDE",
            "INFO": "KEY_INFO", "TOOLS": "KEY_TOOLS", "SOURCE": "KEY_SOURCE",
            "PLAY": "KEY_PLAY", "PAUSE": "KEY_PAUSE", "STOP": "KEY_STOP",
            "FF": "KEY_FF", "REWIND": "KEY_REWIND", "REC": "KEY_REC",
            "VOLUP": "KEY_VOLUP", "VOLDOWN": "KEY_VOLDOWN", "MUTE": "KEY_MUTE",
            "POWER": "KEY_POWER", "POWEROFF": "KEY_POWEROFF", "POWERON": "KEY_POWERON",
            "HDMI1": "KEY_HDMI1", "HDMI2": "KEY_HDMI2", "HDMI3": "KEY_HDMI3", "HDMI4": "KEY_HDMI4",
            "CHUP": "KEY_CHUP", "CHDOWN": "KEY_CHDOWN", "CH_LIST": "KEY_CH_LIST",
            "APP_LIST": "KEY_APP_LIST"
        }

        self.keyboard_mapping = {
            'w': 'KEY_UP', 's': 'KEY_DOWN', 'a': 'KEY_LEFT', 'd': 'KEY_RIGHT',
            'e': 'KEY_ENTER', 'h': 'KEY_HOME', 'm': 'KEY_MENU',
            '+': 'KEY_VOLUP', '-': 'KEY_VOLDOWN', ' ': 'KEY_PAUSE',
            'p': 'KEY_POWER', **{str(i): f"KEY_{i}" for i in range(10)}
        }

    def _load_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                return f.read().strip()
        return None

    def _save_token(self, token):
        with open(self.token_file, "w") as f:
            f.write(token)

    def _generate_token(self):
        return str(int(time.time() % 1000000))

    def connect(self):
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get('event') in ('ms.channel.connect', 'ms.channel.ready'):
                    new_token = data.get("data", {}).get("token")
                    if new_token and new_token != self.token:
                        self.token = new_token
                        self._save_token(new_token)
                    self.is_ready = True
            except:
                pass

        def on_error(ws, error):
            print(f"[!] WebSocket error: {error}")

        def on_close(ws, code, msg):
            print(f"[!] Connection closed ({code}): {msg}")

        def on_open(ws):
            print("[+] Connected to TV")

        self.websocket = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        thread = threading.Thread(target=self.websocket.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
        thread.daemon = True
        thread.start()

        for _ in range(100):
            if self.is_ready:
                return True
            time.sleep(0.1)

        print("[-] Timeout: no response from TV")
        return False

    def send_command(self, method, params=None):
        if not self.websocket:
            print("[-] No active connection")
            return False

        try:
            self.websocket.send(json.dumps({"method": method, "params": params or {}}))
            return True
        except Exception as e:
            print(f"[!] Send failed: {e}")
            return False

    def send_key(self, key, hold_time=0):
        if key in self.key_mapping:
            key = self.key_mapping[key]
        elif key not in self.key_mapping.values():
            print(f"[-] Invalid key: {key}")
            return False

        params = {
            "Cmd": "Click" if hold_time == 0 else "Press",
            "DataOfCmd": key,
            "Option": "false",
            "TypeOfRemote": "SendRemoteKey"
        }

        self.send_command("ms.remote.control", params)
        if hold_time > 0:
            time.sleep(hold_time)
            params["Cmd"] = "Release"
            self.send_command("ms.remote.control", params)

        return True

    def launch_app(self, app_id):
        try:
            res = requests.post(f"http://{self.tv_ip}:8001/api/v2/applications/{app_id}", timeout=10)
            return res.status_code == 200
        except Exception as e:
            print(f"[!] Launch failed: {e}")
            return False

    def get_system_info(self):
        try:
            res = requests.get(f"http://{self.tv_ip}:8001/api/v2/", timeout=3, verify=False)
            return res.json()
        except:
            return None

    def interactive_control(self):
        print("\n[-] Interactive mode active. Press '?' or 'h' for help. 'q' to quit.")
        self._print_help()
        while True:
            key = self._get_keypress()
            if key == 'q':
                break
            elif key in ('?', 'h'):
                self._print_help()
            elif key == 'l':
                self._list_all_commands()
            elif key == 'x':
                self._launch_app_menu()
            elif key == 'c':
                self._custom_command_menu()
            elif key in self.keyboard_mapping:
                self.send_key(self.keyboard_mapping[key])
            else:
                print(f"[!] Unmapped key: {key}")

    def _print_help(self):
        print(r"""
╔═════════════════════════════════════════════════════════╗
║                     COMANDOS DISPONÍVEIS               ║
╠═════════════════════════════════════════════════════════╣
║ w / a / s / d   → Navegação direcional                  ║
║ e               → OK / Enter                            ║
║ + / -           → Volume + / -                          ║
║ espaço          → Play / Pause                          ║
║ p               → Ligar / Desligar TV                   ║
║ 0 a 9           → Teclas numéricas                      ║
║ l               → Listar todos os comandos suportados   ║
║ x               → Abrir menu de aplicativos             ║
║ c               → Enviar comando personalizado          ║
║ h ou ?          → Mostrar este menu de ajuda            ║
║ q               → Sair do modo interativo               ║
╚═════════════════════════════════════════════════════════╝
""")

    def _get_keypress(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _list_all_commands(self):
        print("\n[+] Comandos disponíveis:")
        for k, v in sorted(self.key_mapping.items()):
            print(f"  {k:<10} → {v}")
        print("")

    def _launch_app_menu(self):
        print("\n[-] Aplicativos disponíveis:")
        for name, aid in self.app_list.items():
            print(f"  {name:<12} → {aid}")
        app = input("\n> Nome do app ou ID: ").strip().lower()
        if app in self.app_list:
            self.launch_app(self.app_list[app])
        elif len(app) > 5:
            self.launch_app(app)
        else:
            print("[-] Aplicativo não reconhecido")

    def _custom_command_menu(self):
        print("\n[+] Modo Comando Customizado:")
        print("1. Enviar tecla   2. Enviar método direto")
        choice = input("> Escolha (1/2): ").strip()
        if choice == '1':
            key = input("Tecla: ").strip().upper()
            hold = input("Segurar por (segundos): ").strip()
            self.send_key(key, float(hold) if hold else 0)
        elif choice == '2':
            method = input("Método: ").strip()
            raw = input("Parâmetros (JSON): ").strip()
            try:
                self.send_command(method, json.loads(raw) if raw else None)
            except:
                print("[-] JSON inválido")


def main():
    print(r"""
              █████████   █████████  ███████████   █████████ 
             ███░░░░░███ ███░░░░░███░█░░░███░░░█  ███░░░░░███
            ░███    ░░░ ░███    ░░░ ░   ░███  ░  ███     ░░░ 
            ░░█████████ ░░█████████     ░███    ░███         
             ░░░░░░░░███ ░░░░░░░░███    ░███    ░███         
             ███    ░███ ███    ░███    ░███    ░░███     ███
            ░░█████████ ░░█████████     █████    ░░█████████ 
             ░░░░░░░░░   ░░░░░░░░░     ░░░░░      ░░░░░░░░░  


                                                
   Samsung Smart TV Terminal Controller - by AgniK4i - https://github.com/agnik4i
    """)

    ip = input("TV IP > ").strip()
    controller = SamsungTVController(ip)

    info = controller.get_system_info()
    if info:
        device = info.get("device", {})
        print(f"\nModelo     : {device.get('modelName', 'N/A')}")
        print(f"Nome       : {device.get('name', 'N/A')}")
        print(f"SO         : {device.get('OS', 'N/A')}")
        print(f"Resolução  : {device.get('resolution', 'N/A')}\n")

    if controller.connect():
        controller.interactive_control()

    print("\n[+] Sessão encerrada.")

if __name__ == "__main__":
    main()
