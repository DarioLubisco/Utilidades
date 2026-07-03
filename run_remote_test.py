"""Ejecuta test_connection.py en el servidor remoto."""
import os

import paramiko

HOST = os.environ.get("UTIL_REMOTE_HOST", "10.147.18.4")
USER = os.environ.get("UTIL_REMOTE_USER", "root")
PASSWORD = os.environ.get("DEBIAN_SSH_PASSWORD") or os.environ.get("UTIL_REMOTE_PASSWORD")
if not PASSWORD:
    raise RuntimeError("Define DEBIAN_SSH_PASSWORD o UTIL_REMOTE_PASSWORD en el entorno.")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=20)

sftp = ssh.open_sftp()
sftp.put("test_connection.py", "/root/source/Utilidades/test_connection.py")
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "cd /root/source/Utilidades && python3 test_connection.py", timeout=60
)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:", err)
ssh.close()
