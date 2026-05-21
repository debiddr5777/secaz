
```
                                                         
      _/_/_/  _/_/_/_/    _/_/_/    _/_/    _/_/_/_/_/   
   _/        _/        _/        _/    _/        _/      
    _/_/    _/_/_/    _/        _/_/_/_/      _/         
       _/  _/        _/        _/    _/    _/            
_/_/_/    _/_/_/_/    _/_/_/  _/    _/  _/_/_/_/_/       
                                                         
                                                         
```

# SECAZ — Linux GUI Application Uninstaller

Discover and uninstall Linux GUI applications by scanning `.desktop` files. **apt** and **snap** packages supported, with optional deep cleanup of cache, config, and local state.

## Quick Install (one command)

```bash
curl -sSL https://raw.githubusercontent.com/debiddr5777/secaztool/main/install.sh | bash
```

This clones the repo, installs `secaz` system-wide (or to `~/.local/bin`), adds it to your `PATH` automatically, and installs `fzf` for interactive multi-select.

After install, open a new terminal and run:

```bash
secaz
```

## Manual Install

```bash
git clone https://github.com/debiddr5777/secaztool.git
cd secaztool
pip install -e .
```

## Usage

### Interactive Menu

```bash
secaz
```

Launches a TUI to list all apps (fzf multi-select), fuzzy-search, or view help.

### Fuzzy-Search & Uninstall

```bash
secaz --uninstall firefox
secaz firefox              # shorter form
secaz firefox --full       # deep clean: cache, config, local state
```

Any unknown subcommand is treated as an app name:

```bash
secaz "visual studio code"
secaz discord --full
```

## How It Works

1. Scans `.desktop` files in `/usr/share/applications`, `~/.local/share/applications`, and `/var/lib/snapd/desktop/applications`.
2. Resolves the underlying package manager (`dpkg`/`apt` or `snap`) for each app.
3. Runs `sudo apt-get remove` or `sudo snap remove` to uninstall.
4. With `--full`, also removes `~/.cache/<app>`, `~/.config/<app>`, `~/.local/share/<app>`, `~/snap/<app>`, and `/tmp/<app>`.

## Requirements

- Linux (Debian/Ubuntu/Fedora/Arch or any distro with apt, dnf, or pacman)
- Python 3.8+
- `sudo` access (for package removal)
- `fzf` optional — enables multi-select in interactive mode
