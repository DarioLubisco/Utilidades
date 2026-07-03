"""Despliega Utilidades a 10.147.18.4 via SSH/SFTP."""
from __future__ import annotations

import os
from pathlib import Path

import paramiko

REMOTE_HOST = os.environ.get("UTIL_REMOTE_HOST", "10.147.18.4")
REMOTE_USER = os.environ.get("UTIL_REMOTE_USER", "root")
REMOTE_PASSWORD = os.environ.get("DEBIAN_SSH_PASSWORD") or os.environ.get("UTIL_REMOTE_PASSWORD")
REMOTE_DIR = "/root/source/Utilidades"

LOCAL_DIR = Path(__file__).resolve().parent
SKIP = {"deploy_to_remote.py", "__pycache__"}


def main():
    if not REMOTE_PASSWORD:
        raise RuntimeError("Define DEBIAN_SSH_PASSWORD o UTIL_REMOTE_PASSWORD en el entorno.")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASSWORD, timeout=20)

    ssh.exec_command("mkdir -p /root/source/Utilidades")
    sftp = ssh.open_sftp()

    for item in LOCAL_DIR.iterdir():
        if item.name in SKIP or item.name.startswith(".") or item.name == "run_remote_test.py":
            continue
        remote_path = f"{REMOTE_DIR}/{item.name}"
        if item.is_file():
            print(f"Upload: {item.name}")
            sftp.put(str(item), remote_path)
        elif item.is_dir():
            print(f"Skip dir: {item.name}")

    sftp.close()

    # Instalar dependencias en remoto si faltan
    install_cmd = (
        "pip3 install pyodbc paramiko -q 2>/dev/null; "
        "apt-get install -y unixodbc freetds-bin tdsodbc 2>/dev/null || true"
    )
    stdin, stdout, stderr = ssh.exec_command(install_cmd)
    stdout.channel.recv_exit_status()
    print(stdout.read().decode() + stderr.read().decode())

    ssh.exec_command(f"chmod +x {REMOTE_DIR}/run.sh")

    stdin, stdout, stderr = ssh.exec_command(f"ls -la {REMOTE_DIR}")
    print("\n=== Remote contents ===")
    print(stdout.read().decode())

    ssh.close()
    print(f"\nDeployed to {REMOTE_HOST}:{REMOTE_DIR}")


if __name__ == "__main__":
    main()
