# PortHog

![Status](https://img.shields.io/badge/status-100%25-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![License](https://img.shields.io/badge/license-MIT-green)

See what's hogging your ports. Kill it.

## Features

- **Port listing** - All active TCP/UDP connections
- **Process info** - PID and process name for each port
- **Filtering** - Filter by port number or process name
- **Kill button** - Terminate processes directly
- **Auto-refresh** - Updates every 30 seconds (optional)
- **Freeze mode** - Pause updates to inspect
- **Color coding** - System ports highlighted

## Install

```bash
pip install psutil customtkinter
```

## Run

```bash
python main.py
```

For full visibility, run as administrator.

## Usage

1. Launch (admin recommended for full access)
2. See all open ports and their processes
3. Filter by typing port number or process name
4. Click "Kill" to terminate a process

### Tips

- System ports (<1024) shown in red
- LISTEN state shown in green
- Frozen mode keeps display stable while you work
- Auto-refresh can be toggled off

## Why This Exists

"Port already in use" - but by what? This shows you immediately, and lets you kill it without opening Task Manager and hunting.

## License

MIT
