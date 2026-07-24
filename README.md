# Xiaomi TV CLI

A command-line utility for discovering, diagnosing, and optimizing Xiaomi Android TV devices over ADB.

## Features

- Automatically discovers Android TV devices on the local network
- Connects to TVs over wireless ADB
- Displays device model, Android version, SDK version, and launcher
- Checks the current optimization status
- Disables unnecessary Xiaomi and Google packages
- Restores previously disabled packages
- Uses editable YAML optimization profiles
- Provides interactive Android TV setup instructions
- Works without root access or custom firmware

## Requirements

- macOS or Linux
- Python 3.11 or newer
- Android Platform Tools (`adb`)
- TV and computer connected to the same local network

Install ADB on macOS:

```bash
brew install android-platform-tools
```

## Android TV setup

Before using Xiaomi TV CLI:

1. Open **Settings → About**
2. Press **Build** 7 times to enable Developer options
3. Return to Settings and open **Developer options**
4. Enable **USB debugging**
5. Make sure the TV is awake and connected to the same Wi-Fi network as your computer

Some Xiaomi firmware versions do not provide a separate Wireless debugging option. Enabling USB debugging is usually sufficient.

## Installation from source

Clone the repository:

```bash
git clone git@github.com:Razuvaev/xiaomi-tv-cli.git
cd xiaomi-tv-cli
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
pip install -e ".[dev]"
```

## Usage

Show available commands:

```bash
tvctl --help
```

### Discover TVs

```bash
tvctl discover
```

Example:

```text
Scanning 192.168.1.0/24 on port 5555...
Reading device information...

                    Found 2 device(s)
┏━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ # ┃ Manufacturer ┃ Model      ┃ Android ┃ IP address   ┃
┡━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1 │ Xiaomi       │ MiTV-MOOQ0 │ 11      │ 192.168.1.40 │
│ 2 │ Xiaomi       │ MiTV-MSSP3 │ 10      │ 192.168.1.61 │
└───┴──────────────┴────────────┴─────────┴──────────────┘
```

### Connect automatically

```bash
tvctl connect
```

When only one TV is found, it is selected automatically. When multiple TVs are found, the utility asks which one to use.

You can also connect using an explicit IP address:

```bash
tvctl connect 192.168.1.40
```

### Show device status

```bash
tvctl status
```

### Run diagnostics

```bash
tvctl doctor
```

The doctor command checks packages from the selected optimization profile and displays an optimization score.

### Optimize the TV

```bash
tvctl optimize
```

Apply changes without confirmation:

```bash
tvctl optimize --yes
```

### Restore disabled packages

```bash
tvctl restore
```

Restore without confirmation:

```bash
tvctl restore --yes
```

## Safe optimization profile

The default profile currently disables optional components such as:

- PatchWall
- Mi Channel
- Mi Gallery
- Mi Music
- Xiaomi analytics and statistics
- Xiaomi Web Content
- Google Play Games
- Google TV Movies
- Google Assistant
- Leanback recommendations

System-critical packages, OTA update services, TV inputs, HDMI services, Bluetooth, Google Play Services, and the Android TV launcher are not disabled.

## Profiles

Optimization profiles are stored in the `profiles` directory.

Use a custom profile:

```bash
tvctl doctor --profile profiles/safe.yaml
tvctl optimize --profile profiles/safe.yaml
tvctl restore --profile profiles/safe.yaml
```

## Development

Run the linter:

```bash
ruff check .
```

Run tests:

```bash
pytest
```

## Safety

Xiaomi TV CLI uses:

```bash
pm disable-user --user 0
```

Packages are disabled only for the current Android user. They are not removed from the system partition and can be restored using:

```bash
tvctl restore
```

No root access is required.

## License

MIT
