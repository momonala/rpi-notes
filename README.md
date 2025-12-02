# Raspberry Pi Setup Notes

Personal notes for Raspberry Pi setup and configuration. Because I have to look this up every time.

## Contents

- [SSH Setup](#ssh-setup)
- [Conda Installation](#conda-installation)
- [System Updates](#system-updates)
- [Shell Configuration](#shell-configuration)
- [Git Authentication](#git-authentication)
- [SystemD Services](#systemd-services)
- [Rsync](#rsync)
- [Cloudflare Tunnel](#cloudflare-tunnel)
- [Other Tips](#other-tips)

> **See also:** [README.servicemonitor.md](README.servicemonitor.md) - Technical spec for the Service Monitor dashboard app

---

## SSH Setup

### Headless SSH (first boot)
- create the ssh file in the Pi SD card:
```bash
mkdir /Volumes/system-boot/boot
touch /Volumes/system-boot/boot/ssh
```

- get IP address of new headless Pi. (assuming username==`mnalavadi`) One of:
```bash
ping mnalavadi.local
nmap -sn 192.168.0.0/24
``` 

Assuming IP is `192.168.0.184`
- SSH: `ssh mnalavadi@192.168.0.184`

### Enable Root Login & Password Auth
set new password for root:
```bash
sudo passwd root
```

edit the SSH configuratiopn `sudo nano /etc/ssh/sshd_config` to these lines:
```bash
PermitRootLogin prohibit-password
PermitRootLogin yes
PasswordAuthentication yes
```
restart SSH: `sudo systemctl restart ssh`

SSH: `ssh root@192.168.0.184`

### SSH Keys (passwordless login)
- make RSA keys on computer A.
   -  should have them already. Check if file `/Users/mnalavadi/.ssh/id_rsa.pub` exists. Skip step if so.
   - else: `ssh-keygen -t rsa`
- in Pi make SSH dir: `ssh mnalavadi@192.168.0.184  mkdir -p .ssh`
- dump computer A public keys into auth folder on Pi:
   - `cat /Users/mnalavadi/.ssh/id_rsa.pub | ssh mnalavadi@192.168.0.184 'cat >> .ssh/authorized_keys'`

---

## Conda Installation

note: do this on a laptop then scp to Pi
note: run `-b` to skip license agreement

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh -b
~/miniconda3/bin/conda init

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

---

## System Updates
See `update_system.sh`

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
alias sd='conda deactivate'
alias ca='conda activate'

alias gps="sd && ca incognita && cd /home/mnalavadi/incognita"
```

---

## Git Authentication

### Quick Way (copy from local machine)
the short way:
```
scp ~/.gitconfig mnalavadi@192.168.0.184:/home/mnalavadi/.gitconfig
scp ~/.git-credentials mnalavadi@192.168.0.184:/home/mnalavadi/.git-credentials
```

### Manual Setup
- `nano ~/.gitconfig`
```
[user]
	email = <GIT EMAIL>
	name = <GIT USERNAME>
[filter "lfs"]
	clean = git-lfs clean -- %f
	smudge = git-lfs smudge -- %f
	process = git-lfs filter-process
	required = true
[alias]
	co = checkout
[pager]
	branch = false
[credential]
	helper = store
```
- Copy auth token from local machine: `nano ~/.git-credentials`

---

## SystemD Services

### Create a Service
- create file: `/lib/systemd/system/<SERVICE_NAME>.service`
  
```
[Unit]
 Description= ...
 After=multi-user.target

 [Service]
 WorkingDirectory=/home/mnalavadi/<SOME DIRECTORY>
 Type=idle
 ExecStart=</usr/bin/python3 | python env path> <SOME COMMAND>
 User=mnalavadi

 [Install]
 WantedBy=multi-user.target
```

### Enable & Start
```
sudo chmod 644 /lib/systemd/system/<SERVICE_NAME>.service

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

sudo systemctl enable <SERVICE_NAME>.service

sudo reboot
```

### View Logs
```
journalctl -u <SERVICE_NAME>.service
-f [to follow]
-r [reverse order]
```

---

## Rsync
sync computer --> pi
- `rsync -avu . mnalavadi@192.168.0.184:<PI_DIRECTORY/>`

sync pi --> computer
- `rsync -avu mnalavadi@192.168.0.184:<PI_DIRECTORY/> .`

---

## Cloudflare Tunnel

See [cloudflared/README.md](cloudflared/README.md)

---

## Other Tips

### Mount a USB Drive
- https://raspberrytips.com/mount-usb-drive-raspberry-pi/

### Samba (Networked Drive)

- https://pimylifeup.com/raspberry-pi-samba/

### Remote Jupyter

Run Jupyter on Pi, access from another machine:
```bash
jupyter notebook --ip 192.168.0.184
```

### Disable IPv6

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```
