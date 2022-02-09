## Raspberry Pi Notes
because I have to go through this too many times

### Setup

#### Headless SSH:
- create the ssh file in the Pi SD card: `touch /Volumes/boot/ssh`
- create a file called `wpa_supplicant.conf` with the contents:
```
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="NETWORK-NAME"
    psk="NETWORK-PASSWORD"
}
```
- get IP address of new headless Pi: `ping raspberrypi.local`
- SSH: `ssh pi@192.168.0.184`

#### Use RSA Keys for SSH authentication (no more password!):
- make RSA keys on computer A.
   -  should have them already. Check if file `/Users/mnalavadi/.ssh/id_rsa.pub` exists. Skip step if so.
   - else: `ssh-keygen -t rsa`
- in Pi make SSH dir: `ssh pi@IP_ADDRESS  mkdir -p .ssh`
- dump computer A public keys into auth folder on Pi:
   - `cat /Users/mnalavadi/.ssh/id_rsa.pub | ssh pi@IP_ADDRESS 'cat >> .ssh/authorized_keys'`
- no more password needed on SSH!

#### Basic updates & software
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install nano git python3-pip -y
```

```
pip install -U jupyter ipython
```
- note: you can run jupyter on the PI but interact on another computer by setting the host:
  - ` jupyter notebook --ip IP_ADDRESS`

#### useful aliases and env vars
- add to ~/.bashrc
```
alias c=clear
alias cd..='cd ..'
alias g=git
alias gb='git branch'
alias gp='git push'
alias la='ls -lAh'
alias nanobash='nano ~/.bashrc'
alias sourcebash='source ~/.bashrc'

export PATH="$HOME/.local/bin:$PATH"
```

#### Authenticate Git (no password needed on pushes!)
- `nano ~/.gitconfig`
```
[user]
	email = mnalavadi@gmail.com
	name = momonala
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
- `nano ~/.git-credentials`
  - copy auth line from computer A

#### Mount a USB drive:
- https://raspberrytips.com/mount-usb-drive-raspberry-pi/

#### Setup Networked Drive:
- https://pimylifeup.com/raspberry-pi-samba/
