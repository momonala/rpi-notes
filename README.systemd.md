# SystemD Services

## Create a Service

Create file: `/lib/systemd/system/<SERVICE_NAME>.service`

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

## Enable & Start

```
sudo chmod 644 /lib/systemd/system/<SERVICE_NAME>.service

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

sudo systemctl enable <SERVICE_NAME>.service

sudo reboot
```

## View Logs

```
journalctl -u <SERVICE_NAME>.service
-f [to follow]
-r [reverse order]
```

