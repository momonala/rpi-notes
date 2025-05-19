## Raspberry Pi setup notes
because I have to go through this too many times

### Headless SSH:
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

### Enable SSH & Password Authentication for root
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

### Use RSA Keys for SSH authentication (no more password!):
- make RSA keys on computer A.
   -  should have them already. Check if file `/Users/mnalavadi/.ssh/id_rsa.pub` exists. Skip step if so.
   - else: `ssh-keygen -t rsa`
- in Pi make SSH dir: `ssh mnalavadi@192.168.0.184  mkdir -p .ssh`
- dump computer A public keys into auth folder on Pi:
   - `cat /Users/mnalavadi/.ssh/id_rsa.pub | ssh mnalavadi@192.168.0.184 'cat >> .ssh/authorized_keys'`

### Download and install latest Conda:

note: do this on a laptop then scp to Pi
note: run `-b` to skip license agreement

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh -b
~/miniconda3/bin/conda init
```

### Basic updates & software
See `update_system.sh`

[update python version](https://stackoverflow.com/questions/64718274/how-to-update-python-in-raspberry-pi)

### useful aliases and env vars
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

alias train_tracker="sd && ca train_tracker && cd /home/mnalavadi/train_tracker"
alias bathroom_button="sd && ca bathroom_button && cd /home/mnalavadi/bathroom_button"
alias gps="sd && ca incognita && cd /home/mnalavadi/incognita"
```

### Authenticate Git (no password needed on pushes!)
the short way:
```
scp ~/.gitconfig mnalavadi@192.168.0.184:/home/mnalavadi/.gitconfig
scp ~/.git-credentials mnalavadi@192.168.0.184:/home/mnalavadi/.git-credentials
```

Or the long way...
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
- copy auth line from computer A to pi `nano ~/.git-credentials`
 
---
### SystemD:
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

- Start the services
```
sudo chmod 644 /lib/systemd/system/<SERVICE_NAME>.service

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

sudo systemctl enable <SERVICE_NAME>.service

sudo reboot
```

- View logs
```
journalctl -u <SERVICE_NAME>.service
-f [to follow]
-r [reverse order]
```

### Rysnc:
sync computer --> pi
- `rsync -avu . mnalavadi@192.168.0.184:<PI_DIRECTORY/>`

sync pi --> computer
- `rsync -avu mnalavadi@192.168.0.184:<PI_DIRECTORY/> .`

### Other:
#### Mount a USB drive:
- https://raspberrytips.com/mount-usb-drive-raspberry-pi/

#### Setup Networked Drive:
- https://pimylifeup.com/raspberry-pi-samba/

#### Notes
- note: you can run jupyter on the PI but interact on another computer by setting the host:
  - ` jupyter notebook --ip 192.168.0.184`

  ### CloudFlare
  See [here](cloudflared/README.md)
  
  ### Disable ipv6

sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
