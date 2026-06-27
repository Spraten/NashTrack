# Nash Track Web

React/Vite version of the Nash Track dashboard.

## Run

From the project root:

```powershell
python main.py
```

That starts the local Vite web server, waits for it to answer, and opens Nash
Track in an app-style Edge/Chrome window when one is available. The launcher
opens the app at 800x480 by default so it matches the target 7-inch display.

To test a different app-window size:

```powershell
$env:NASH_TRACK_WINDOW_WIDTH = "1024"
$env:NASH_TRACK_WINDOW_HEIGHT = "600"
python main.py
```

To launch the old Kivy UI for comparison:

```powershell
python main.py --kivy
```

To run the web server manually:

```powershell
cd "C:\Users\nisse\Documents\New project 3\web"
$nodeDir = "$PWD\.tools\node-v24.16.0-win-x64"
$env:Path = "$nodeDir;$env:Path"
& "$nodeDir\npm.cmd" install
& "$nodeDir\npm.cmd" run dev
```

Open `http://localhost:5173`.

This repo uses a portable Node install under `web\.tools` because Node/npm is not
currently installed globally on this Windows profile.

The UI includes a compact kiosk breakpoint for the 7-inch Raspberry Pi display
target: 800x480, with the layout held as a tight app dashboard instead of
collapsing into a normal mobile webpage.

This first pass is a static UI shell that matches the sports-dashboard direction. The next step is wiring the existing ESPN/OpenF1/weather data flows into React.
