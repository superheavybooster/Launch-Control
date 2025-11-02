# StarbaseSim Launch Control

> A small desktop control panel and telemetry bridge for the StarbaseSim game.

This repository contains a WebSocket proxy server, a small flight-logic module, and a PyWebView-based desktop UI that shows telemetry and basic launch controls.

## Features
- WebSocket server that forwards telemetry from the StarbaseSim game to a local HTML UI
- Flight software helpers and scripts (as Python async code)
- Desktop UI using `pywebview` with `LaunchControl.html`
- Build script (`build.bat`) that packages the app with PyInstaller

## Quick start (Windows, PowerShell)

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app (GUI + server + flight software)

```powershell
python Main.py
```

3. Run server only

```powershell
python Main.py --server
```

4. Run flight software only (useful for development)

```powershell
python Main.py --flight
```

5. Build an executable (Windows)

Open `build.bat` in a cmd/powershell window. The script will ensure required tools are installed and run PyInstaller to create a single-file executable. Recommended: run inside a virtualenv.

## Tests

Run tests with:

```powershell
pytest -q
```

## Troubleshooting
- If the UI shows "Disconnected", make sure `Server.py` is running and StarbaseSim (the game) is listening on localhost:12345.
- If imports for `websockets` or `pywebview` fail, install requirements in an activated venv as shown above.

## Notes & next steps
- Add CI to run tests automatically (a GitHub Actions workflow is included).
- Consider improving packaging (include assets, icons) and adding more test coverage for flight scripts.

## License
Small personal project — add your preferred license if you want to publish.
