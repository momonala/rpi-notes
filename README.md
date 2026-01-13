# Raspberry Pi Setup Notes

[![CI](https://github.com/momonala/service-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/momonala/service-monitor/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/momonala/service-monitor/branch/main/graph/badge.svg)](https://codecov.io/gh/momonala/service-monitor)

Personal notes for Raspberry Pi setup and configuration. Because I have to look this up every time.

## Configuration

Export your Pi hostname/IP and username:
```bash
export RPI_HOST="mnalavadi@192.168.0.184"
```

## Contents

- [Project Naming Convention Tool](#project-naming-convention-tool)
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

## Project Naming Convention Tool

**Location:** `../rename_project_unified.sh` (at projects root)

A unified tool to standardize project directory names and systemd service files across all projects.

**Naming Convention:**
```
Format: projects_<PROJECT><_SUB-SERVICE>.service
- PROJECT: alphanumeric with dashes only (no underscores)
- SUB-SERVICE: optional, starts with underscore, can contain dashes

Examples:
- energy_monitor → energy-monitor
- projects_energy_monitor.service → projects_energy-monitor.service
- projects_inspector-detector_site.service → projects_inspector-detector_site.service
```

**Usage:**
```bash
# From the projects root directory
cd /Users/mnalavadi/code/projects

# Dry run to see what would change
./rename_project_unified.sh --dry-run

# Interactive rename (recommended)
./rename_project_unified.sh

# Follow the prompts to rename each project
```

**What it does:**
- Scans all projects and identifies naming violations
- Renames project directories using `git mv`
- Updates all service files and references in:
  - Service files (WorkingDirectory paths)
  - pyproject.toml (project name)
  - install/install.sh (service_name variable)
  - README files
  - Test fixtures (src/canned_info.py)
- Generates Pi migration commands script
- Provides interactive confirmation for each project

**Single Project Rename (legacy):**

The `install/rename_project_local.sh` and `install/rename_service_pi.sh` scripts are still available for single-project renames:
```bash
# From within a single project directory
./install/rename_project_local.sh old_name new-name

# Then on the Pi (after pushing changes)
./install/rename_service_pi.sh old_name new-name
```

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
