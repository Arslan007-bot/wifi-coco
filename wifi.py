# ── coco.py ──────────────────────────
#!/usr/bin/env python3

import os
import sys
import socket
import subprocess
import threading
import time
from datetime import datetime

class COCOTerminal:
    def __init__(self):
        self.running = True
        self.target_host = None
        self.target_port = 4444
        self.sock = None
        self.connected = False
        self.history = []
        
    def banner(self):
        banner_text = """
╔════════════════════════════════════════════╗
║            COCO Terminal v1.0              ║
║          Remote Command Execution          ║
╚════════════════════════════════════════════╝
        """
        print(banner_text)
    
    def get_local_ip(self):
        """Get local WiFi IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_listener(self):
        """Start listening for incoming connections"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(("0.0.0.0", self.target_port))
            self.sock.listen(1)
            print(f"[+] COCO listening on port {self.target_port}...")
            print(f"[+] Local IP: {self.get_local_ip()}\n")
            
            while self.running:
                try:
                    conn, addr = self.sock.accept()
                    print(f"[+] COCO connection from {addr[0]}:{addr[1]}")
                    self.connected = True
                    self.handle_client(conn, addr)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[!] Connection error: {e}")
                    
        except Exception as e:
            print(f"[!] Listener error: {e}")
        finally:
            if self.sock:
                self.sock.close()
    
    def handle_client(self, conn, addr):
        """Handle client connection and execute commands"""
        try:
            # Send welcome message
            welcome = f"\n[+] Welcome to COCO Terminal\n[+] Connected from {addr[0]}\n\n"
            conn.send(welcome.encode())
            
            while self.connected:
                try:
                    # Receive command
                    data = conn.recv(1024).decode().strip()
                    
                    if not data:
                        continue
                    
                    # Log command
                    self.history.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'source': addr[0],
                        'command': data
                    })
                    
                    print(f"[COCO] [{addr[0]}] $ {data}")
                    
                    # Handle built-in commands
                    if data.lower() == "exit":
                        conn.send(b"[+] COCO disconnecting...\n")
                        break
                    
                    elif data.lower() == "clear":
                        conn.send(b"\033[2J\033[H")
                        continue
                    
                    elif data.lower().startswith("help"):
                        self.send_help(conn)
                        continue
                    
                    elif data.lower().startswith("whoami"):
                        result = subprocess.check_output("whoami", shell=True).decode()
                        conn.send(result.encode())
                        continue
                    
                    elif data.lower().startswith("pwd"):
                        result = subprocess.check_output("pwd", shell=True).decode()
                        conn.send(result.encode())
                        continue
                    
                    elif data.lower().startswith("ifconfig"):
                        result = subprocess.check_output("ifconfig", shell=True).decode()
                        conn.send(result.encode())
                        continue
                    
                    # Execute system command
                    else:
                        try:
                            result = subprocess.check_output(data, shell=True, stderr=subprocess.STDOUT).decode()
                            conn.send(result.encode())
                        except subprocess.CalledProcessError as e:
                            error = f"[!] Command error: {e.output.decode()}\n"
                            conn.send(error.encode())
                        except Exception as e:
                            error = f"[!] Error executing command: {str(e)}\n"
                            conn.send(error.encode())
                    
                    # Send prompt
                    conn.send(b"\n$ ")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[!] Handler error: {e}")
                    break
        
        finally:
            print(f"[-] COCO disconnected: {addr[0]}")
            conn.close()
            self.connected = False
    
    def send_help(self, conn):
        help_text = """
╔════════════════════════════════════════╗
║     COCO Terminal - Available Commands ║
╚════════════════════════════════════════╝

Built-in Commands:
  help              - Show this help message
  exit              - Close connection
  clear             - Clear screen
  whoami            - Display current user
  pwd               - Print working directory
  ifconfig          - Show network configuration
  history           - Show command history

System Commands:
  ls                - List directory contents
  cat <file>        - Display file contents
  ps                - Show running processes
  netstat           - Show network statistics
  ping <host>       - Ping a host
  wget <url>        - Download file
  echo <text>       - Print text
  id                - Show user/group info
  uname -a          - Show system info
  date              - Show current date/time

Any shell command can be executed directly.
Type 'exit' to disconnect from COCO.

"""
        conn.send(help_text.encode())
    
    def start_client(self, host, port=4444):
        """Connect to COCO Terminal server"""
        try:
            print(f"[*] COCO connecting to {host}:{port}...")
            self.target_host = host
            self.target_port = port
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            print(f"[+] COCO connected to {host}:{port}\n")
            
            # Receive welcome
            welcome = sock.recv(1024).decode()
            print(welcome)
            
            # Interactive shell
            while True:
                try:
                    cmd = input("$ ")
                    
                    if not cmd:
                        continue
                    
                    sock.send((cmd + "\n").encode())
                    
                    # Receive output
                    output = sock.recv(4096).decode()
                    print(output, end="")
                    
                    if cmd.lower() == "exit":
                        break
                
                except KeyboardInterrupt:
                    sock.send(b"exit\n")
                    break
                except Exception as e:
                    print(f"[!] COCO error: {e}")
                    break
            
            sock.close()
            print("\n[-] COCO disconnected")
        
        except Exception as e:
            print(f"[!] COCO connection failed: {e}")
    
    def show_history(self):
        """Display command history"""
        if not self.history:
            print("[!] No commands in COCO history")
            return
        
        print("\n╔═══════════════════════════════════════════════════════╗")
        print("║              COCO Command History                     ║")
        print("╚═══════════════════════════════════════════════════════╝\n")
        
        for entry in self.history:
            print(f"[{entry['timestamp']}] {entry['source']:15} $ {entry['command']}")
        
        print()

def main():
    if len(sys.argv) < 2:
        print("╔════════════════════════════════════════════╗")
        print("║            COCO Terminal v1.0             ║")
        print("╚════════════════════════════════════════════╝\n")
        print("Usage:")
        print("  python3 coco.py server              # Start COCO server mode")
        print("  python3 coco.py client <host>       # Connect to COCO server")
        print("  python3 coco.py client <host> <port> # Connect with custom port\n")
        print("Example:")
        print("  # Terminal 1 (server): python3 coco.py server")
        print("  # Terminal 2 (client): python3 coco.py client 192.168.1.100\n")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "server":
        terminal = COCOTerminal()
        terminal.banner()
        
        try:
            terminal.start_listener()
        except KeyboardInterrupt:
            print("\n[*] COCO shutting down...")
            terminal.running = False
        finally:
            terminal.show_history()
    
    elif mode == "client":
        if len(sys.argv) < 3:
            print("[!] COCO client mode requires host address")
            print("Usage: python3 coco.py client <host> [port]")
            sys.exit(1)
        
        host = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 4444
        
        terminal = COCOTerminal()
        terminal.banner()
        terminal.start_client(host, port)
    
    else:
        print(f"[!] Unknown COCO mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()