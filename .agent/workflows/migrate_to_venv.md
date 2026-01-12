---
description: Migrate Vetaris VPS deployment to use Python Virtual Environment (venv)
---

This workflow guides you through setting up a Python virtual environment on your VPS and updating the service to run from it.

### 1. Create Virtual Environment
Run these commands in your project root (`/var/www/vetaris.com`):

```bash
# Install venv module if needed (Debian/Ubuntu)
sudo apt install python3-venv

# Create the virtual environment named 'venv'
python3 -m venv venv
```

### 2. Install Dependencies in Venv
Activate the environment and install requirements:

```bash
# Activate venv
source venv/bin/activate

# Install packages (pip works freely here!)
pip install -r requirements.txt

# Verify installation
python3 verify_db.py

# Deactivate
deactivate
```

### 3. Update Systemd Service
We need to point the service to the python executable **inside** the venv.

Edit the service file:
```bash
sudo nano /etc/systemd/system/vetaris.service
```

Change the `ExecStart` line to use the venv python:
```ini
# OLD: ExecStart=/usr/bin/python3 /var/www/vetaris.com/src/server.py
# NEW:
ExecStart=/var/www/vetaris.com/venv/bin/python3 /var/www/vetaris.com/src/server.py
```

### 4. Restart Service
Reload configs and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart vetaris.service
sudo systemctl status vetaris.service
```
