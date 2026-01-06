# Raspberry Pi Setup Notes

Personal notes for Raspberry Pi setup and configuration. Because I have to look this up every time.

## Configuration

Export your Pi hostname/IP and username:
```bash
export RPI_HOST="mnalavadi@192.168.0.184"
```

## Contents

- [SSH Setup](#ssh-setup)
- [System Updates & Initial Setup](#system-updates--initial-setup)
- [Shell Configuration](#shell-configuration)
- [Git Authentication](#git-authentication)
- [Rsync](#rsync)

> **See also:**
> - [README.servicemonitor.md](README.servicemonitor.md) - Technical spec for the Service Monitor dashboard app
> - [README.systemd.md](README.systemd.md) - SystemD service management guide
> - [cloudflared/README.md](cloudflared/README.md) - Cloudflare setup

---

## SSH Setup

- get IP address of new headless Pi. (assuming username==`mnalavadi`) One of:
```bash
ping mnalavadi.local
nmap -sn 192.168.0.0/24
``` 

Assuming IP is `192.168.0.184`
- SSH: `ssh $RPI_HOST`

---

## System Updates & Initial Setup
Run `install.sh` to update the system and install dependencies:

```bash
./install.sh
```

This script will:
- Update package lists and upgrade all packages
- Install git and bc
- Remove unused packages and clean up
- Perform firmware updates
- Install/update uv (Python package manager)

[Update Python version](https://stackoverflow.com/questions/64718274/how-to-update-python-in-raspberry-pi)

---

## Shell Configuration

### Aliases
- add to `nano ~/.bashrc`
```
alias c=clear
alias cd..='cd ..'
alias ..='cd ..'
alias g=git
alias gb='git branch'
alias gp='git push'
alias la='ls -lAh'
alias nanobash='nano ~/.bashrc'
alias sourcebash='source ~/.bashrc'
```

---

## Git Authentication

### Quick Way (copy from local machine):
```
scp ~/.gitconfig $RPI_HOST:/home/mnalavadi/.gitconfig
scp ~/.git-credentials $RPI_HOST:/home/mnalavadi/.git-credentials
```

---

## Rsync
sync computer --> pi
- `rsync -avu . $RPI_HOST:<PI_DIRECTORY/>`

sync pi --> computer
- `rsync -avu $RPI_HOST:<PI_DIRECTORY/> .`
