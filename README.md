# Raspberry Pi PLC Communication Setup

This project enables communication between a Raspberry Pi and a PLC using Ethernet. It requires setting a static IP for the Ethernet interface and setting up a Python virtual environment.

---

## 📍 1. Set a Static IP Address (Ethernet)

This project assumes the PLC uses IP `192.168.2.1`. The Raspberry Pi must be manually configured to be on the same subnet.

### Steps:

🛠️ Dual-NIC Configuration (Wi-Fi + Static Ethernet for PLC)

This setup configures:

- wlan0 for internet access (via DHCP)
- eth0 with a static IP (192.168.2.10) for direct communication with a PLC (192.168.2.1)

📋 Prerequisites

- Raspberry Pi OS or Debian-based distro using NetworkManager
- PLC connected directly via Ethernet cable to Raspberry Pi

🔧 Configuration Steps

1. Ensure eth0 is not managed by dhcpcd:
   Edit:
     sudo nano /etc/dhcpcd.conf
   Comment out or remove any 'interface eth0' section.

2. Identify the Ethernet connection name:
     ```Bash
     nmcli connection show
     ```

3. Set static IP for eth0 using NetworkManager:
   ```Bash
   sudo nmcli connection modify "Wired connection 1" \
      ipv4.addresses 192.168.2.10/24 \
      ipv4.method manual \
      connection.autoconnect yes
   ```

4. Activate the connection:
   ```Bash
   sudo nmcli connection up "Wired connection 1"
   ```

5. Verify:
   ```Bash
     ip a show eth0
     ping 192.168.2.1
   ```

The above setup is persistent across reboots and isolates PLC communication from internet traffic.

---

## 🐍 3. Python Project Setup with Poetry

After cloning the project:

```bash
git clone https://github.com/Archegon/Elixir_backend.git
cd plc-comm-test
```

### Install Poetry (if you don't have it):

On Windows PowerShell:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```
Or with pipx:
```powershell
pipx install poetry
```

For Raspberry Pi / Linux:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to Path:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

### Install dependencies and set up the environment:

```bash
poetry install
```

🔧 Poetry Install Hangs or Keyring Errors
If poetry install hangs or throws keyring-related errors in headless or minimal environments (e.g. Ubuntu server, Docker), apply the following fix:

Disable Python keyring system:
```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

To make it permanent, add the line to your shell config (e.g. ~/.bashrc, ~/.zshrc):
```bash
echo 'export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring' >> ~/.bashrc
source ~/.bashrc
```

### Activate the Poetry environment:

```bash
poetry shell
```

Or run commands inside the environment directly:

```bash
poetry run python main.py
```

### (Optional) Select the Poetry environment in your editor (e.g., VS Code):

1. Run:
   ```bash
   poetry env info --path
   ```
2. In VS Code, open the Command Palette (`Ctrl+Shift+P`), type "Python: Select Interpreter", and choose the interpreter matching the path above.

---

## ✅ Final Notes

* Ensure the PLC is powered and reachable at `192.168.2.1`.
* Test connectivity:

  ```bash
  ping 192.168.2.1
  ```
* You may add an `activate.sh` script to simplify venv activation.