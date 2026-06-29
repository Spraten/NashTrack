from __future__ import annotations

import os
import json
import shutil
import stat
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
PORT = int(os.environ.get("NASH_TRACK_PORT", "5173"))
HOST = os.environ.get("NASH_TRACK_HOST", "127.0.0.1")
URL = f"http://127.0.0.1:{PORT}/"
UPDATER_PORT = int(os.environ.get("NASH_TRACK_UPDATER_PORT", "5183"))
UPDATER_URL = f"http://127.0.0.1:{UPDATER_PORT}/health"
PORTABLE_NODE_DIR = WEB_DIR / ".tools" / "node-v24.16.0-win-x64"
WINDOW_WIDTH = int(os.environ.get("NASH_TRACK_WINDOW_WIDTH", "800"))
WINDOW_HEIGHT = int(os.environ.get("NASH_TRACK_WINDOW_HEIGHT", "480"))
DISPLAY_STATE_FILE = Path(
    os.environ.get(
        "NASH_TRACK_DISPLAY_STATE",
        str(Path.home() / ".config" / "nashtrack" / "display.json"),
    )
)
DISPLAY_MODES = {"alwaysOn", "sleep3"}
DISPLAY_POWER_STATES = {"on", "off"}
DISPLAY_SLEEP_SECONDS = int(os.environ.get("NASH_TRACK_SCREEN_SLEEP_SECONDS", "180"))
AUTOSTART_FILE = Path.home() / ".config" / "autostart" / "nashtrack.desktop"
_updater_server: ThreadingHTTPServer | None = None
_updater_thread: threading.Thread | None = None
_display_lock = threading.Lock()
_display_last_activity = time.monotonic()
_display_sleeping = False
_display_watchdog_thread: threading.Thread | None = None


def _creation_flags() -> int:
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _node_executable() -> Path:
    portable_node = PORTABLE_NODE_DIR / ("node.exe" if os.name == "nt" else "node")
    if portable_node.exists():
        return portable_node

    node_on_path = shutil.which("node")
    if node_on_path:
        return Path(node_on_path)

    raise RuntimeError(
        "Node was not found. Expected the portable Node install at "
        f"{PORTABLE_NODE_DIR}, or a global node executable on PATH."
    )


def _server_is_ready(url: str = URL) -> bool:
    try:
        with urlopen(url, timeout=1.0) as response:
            return 200 <= response.status < 500
    except (OSError, URLError):
        return False


def _updater_is_ready() -> bool:
    try:
        with urlopen(UPDATER_URL, timeout=1.0) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status == 200 and "Nash Track updater" in body
    except (OSError, URLError):
        return False


def _wait_for_server(process: subprocess.Popen[bytes], timeout: float = 20.0) -> None:
    started_at = time.monotonic()
    while time.monotonic() - started_at < timeout:
        if _server_is_ready():
            return
        if process.poll() is not None:
            raise RuntimeError(f"Vite exited early with code {process.returncode}.")
        time.sleep(0.25)

    raise TimeoutError(f"Timed out waiting for Nash Track at {URL}.")


def _run_git_update() -> dict[str, object]:
    git = shutil.which("git")
    if not git:
        return {"ok": False, "message": "Git was not found on PATH."}

    inside = subprocess.run(
        [git, "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {"ok": False, "message": "Nash Track is not inside a Git worktree."}

    remote = subprocess.run(
        [git, "remote", "get-url", "origin"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if remote.returncode != 0:
        return {"ok": False, "message": "No origin remote is configured yet."}

    pull = subprocess.run(
        [git, "pull", "--ff-only"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=120,
    )
    output = "\n".join(part.strip() for part in (pull.stdout, pull.stderr) if part.strip())
    if pull.returncode != 0:
        return {
            "ok": False,
            "message": "Update failed. Commit/stash local changes or check the remote.",
            "output": output,
        }

    return {
        "ok": True,
        "message": "Nash Track is up to date." if "Already up to date" in output else "Nash Track updated. Restart the app to load code changes.",
        "output": output,
    }


def _run_git_update_check() -> dict[str, object]:
    git = shutil.which("git")
    if not git:
        return {"ok": False, "message": "Git was not found on PATH."}

    inside = subprocess.run(
        [git, "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {"ok": False, "message": "Nash Track is not inside a Git worktree."}

    remote = subprocess.run(
        [git, "remote", "get-url", "origin"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if remote.returncode != 0:
        return {"ok": False, "message": "No origin remote is configured yet."}

    branch = subprocess.run(
        [git, "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    branch_name = branch.stdout.strip() if branch.returncode == 0 else "main"

    fetch = subprocess.run(
        [git, "fetch", "--quiet", "origin"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if fetch.returncode != 0:
        output = "\n".join(part.strip() for part in (fetch.stdout, fetch.stderr) if part.strip())
        return {"ok": False, "message": "Could not check GitHub for updates.", "output": output}

    upstream = subprocess.run(
        [git, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    upstream_ref = upstream.stdout.strip() if upstream.returncode == 0 else f"origin/{branch_name}"

    local = subprocess.run(
        [git, "rev-parse", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    remote_head = subprocess.run(
        [git, "rev-parse", upstream_ref],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if local.returncode != 0 or remote_head.returncode != 0:
        return {"ok": False, "message": f"Could not resolve update target {upstream_ref}."}

    local_revision = local.stdout.strip()
    remote_revision = remote_head.stdout.strip()

    behind = subprocess.run(
        [git, "rev-list", "--count", f"{local_revision}..{remote_revision}"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    ahead = subprocess.run(
        [git, "rev-list", "--count", f"{remote_revision}..{local_revision}"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )
    subject = subprocess.run(
        [git, "log", "-1", "--pretty=%s", remote_revision],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=10,
    )

    behind_count = int((behind.stdout or "0").strip() or "0") if behind.returncode == 0 else 0
    ahead_count = int((ahead.stdout or "0").strip() or "0") if ahead.returncode == 0 else 0
    update_available = behind_count > 0 and local_revision != remote_revision

    return {
        "ok": True,
        "updateAvailable": update_available,
        "message": "Update available." if update_available else "Nash Track is up to date.",
        "branch": branch_name,
        "upstream": upstream_ref,
        "behind": behind_count,
        "ahead": ahead_count,
        "localRevision": local_revision,
        "remoteRevision": remote_revision,
        "remoteShort": remote_revision[:7],
        "subject": subject.stdout.strip() if subject.returncode == 0 else "",
        "checkedAt": time.time(),
    }


def _run_display_command(command: list[str], timeout: float = 5.0) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {"ok": False, "message": str(error), "command": command[0]}

    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return {
        "ok": result.returncode == 0,
        "message": output,
        "command": command[0],
        "output": output,
    }


def _wlr_output_name() -> str:
    explicit = os.environ.get("NASH_TRACK_DISPLAY_OUTPUT", "").strip()
    if explicit:
        return explicit

    wlr_randr = shutil.which("wlr-randr")
    if wlr_randr:
        result = _run_display_command([wlr_randr], timeout=3.0)
        for line in str(result.get("output", "")).splitlines():
            if line and not line.startswith(" "):
                return line.split()[0]

    return "DSI-1"


def _x11_output_name() -> str:
    explicit = os.environ.get("NASH_TRACK_DISPLAY_OUTPUT", "").strip()
    if explicit:
        return explicit

    xrandr = shutil.which("xrandr")
    if xrandr and os.environ.get("DISPLAY"):
        result = _run_display_command([xrandr, "--query"], timeout=3.0)
        for line in str(result.get("output", "")).splitlines():
            if " connected" in line:
                return line.split()[0]

    return "DSI-1"


def _display_power_commands(state: str) -> list[list[str]]:
    value = "1" if state == "on" else "0"
    commands: list[list[str]] = []

    vcgencmd = shutil.which("vcgencmd")
    if vcgencmd:
        commands.append([vcgencmd, "display_power", value])

    xset = shutil.which("xset")
    if xset and os.environ.get("DISPLAY"):
        commands.append([xset, "dpms", "force", state])

    xrandr = shutil.which("xrandr")
    if xrandr and os.environ.get("DISPLAY"):
        output = _x11_output_name()
        commands.append([xrandr, "--output", output, "--auto" if state == "on" else "--off"])

    wlr_randr = shutil.which("wlr-randr")
    if wlr_randr:
        commands.append([wlr_randr, "--output", _wlr_output_name(), f"--{state}"])

    wlopm = shutil.which("wlopm")
    if wlopm:
        commands.append([wlopm, f"--{state}", _wlr_output_name()])

    swaymsg = shutil.which("swaymsg")
    if swaymsg:
        commands.append([swaymsg, "output", "*", "dpms", state])

    return commands


def _display_idle_config_commands(mode: str) -> list[list[str]]:
    commands: list[list[str]] = []
    xset = shutil.which("xset")
    if xset and os.environ.get("DISPLAY"):
        if mode == "alwaysOn":
            commands.extend([[xset, "s", "off"], [xset, "s", "noblank"], [xset, "-dpms"]])
        elif mode == "sleep3":
            seconds = str(DISPLAY_SLEEP_SECONDS)
            commands.extend([[xset, "s", seconds, seconds], [xset, "+dpms"], [xset, "dpms", seconds, seconds, seconds]])
    return commands


def _configure_display_idle(mode: str) -> dict[str, object]:
    attempts = [_run_display_command(command, timeout=3.0) for command in _display_idle_config_commands(mode)]
    return {
        "ok": any(result.get("ok") for result in attempts) if attempts else False,
        "attempts": attempts,
    }


def _set_display_power(state: str) -> dict[str, object]:
    global _display_sleeping

    if state not in DISPLAY_POWER_STATES:
        return {"ok": False, "message": f"Unknown display power state: {state}"}

    attempts: list[dict[str, object]] = []
    for command in _display_power_commands(state):
        result = _run_display_command(command)
        attempts.append(result)
        if result.get("ok"):
            with _display_lock:
                _display_sleeping = state == "off"
            return {
                "ok": True,
                "message": f"Display power {state} command sent.",
                "command": result.get("command", command[0]),
                "output": result.get("output", ""),
            }

    return {
        "ok": False,
        "message": "No supported display power command worked on this system.",
        "attempts": attempts,
    }


def _note_display_activity(wake: bool = True) -> dict[str, object]:
    global _display_last_activity

    with _display_lock:
        _display_last_activity = time.monotonic()
        should_wake = wake and _display_sleeping

    if should_wake:
        return _set_display_power("on")
    return {"ok": True, "message": "Display activity recorded."}


def _display_status() -> dict[str, object]:
    now = time.monotonic()
    with _display_lock:
        idle_for = max(0.0, now - _display_last_activity)
        sleeping = _display_sleeping

    mode = _read_display_mode()
    return {
        "ok": True,
        "mode": mode,
        "sleeping": sleeping,
        "idleSeconds": int(idle_for),
        "timeoutSeconds": DISPLAY_SLEEP_SECONDS,
        "secondsUntilSleep": max(0, DISPLAY_SLEEP_SECONDS - int(idle_for)) if mode == "sleep3" else None,
        "powerCommands": [command[0] for command in _display_power_commands("off")],
    }


def _display_watchdog_loop() -> None:
    while True:
        time.sleep(5)
        mode = _read_display_mode()
        if mode != "sleep3":
            with _display_lock:
                sleeping = _display_sleeping
            if sleeping:
                _set_display_power("on")
            continue

        with _display_lock:
            idle_for = time.monotonic() - _display_last_activity
            sleeping = _display_sleeping

        if not sleeping and idle_for >= DISPLAY_SLEEP_SECONDS:
            _set_display_power("off")


def _start_display_watchdog() -> None:
    global _display_watchdog_thread
    if _display_watchdog_thread:
        return

    _note_display_activity(wake=False)
    _display_watchdog_thread = threading.Thread(
        target=_display_watchdog_loop,
        name="NashTrackDisplayWatchdog",
        daemon=True,
    )
    _display_watchdog_thread.start()


def _test_display_sleep() -> dict[str, object]:
    result = _set_display_power("off")
    if not result.get("ok"):
        return result

    def wake_later() -> None:
        time.sleep(10)
        _note_display_activity(wake=True)

    threading.Thread(target=wake_later, name="NashTrackDisplayWakeTest", daemon=True).start()
    return {
        "ok": True,
        "message": "Display sleep test started. The screen should wake automatically in 10 seconds.",
        "command": result.get("command"),
        "output": result.get("output", ""),
    }


def _save_display_mode(mode: str) -> dict[str, object]:
    if mode not in DISPLAY_MODES:
        return {"ok": False, "message": f"Unknown display mode: {mode}"}

    try:
        DISPLAY_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DISPLAY_STATE_FILE.write_text(
            json.dumps({"mode": mode, "updatedAt": time.time()}, indent=2),
            encoding="utf-8",
        )
    except OSError as error:
        return {"ok": False, "message": f"Display mode could not be saved: {error}"}

    response: dict[str, object] = {
        "ok": True,
        "mode": mode,
        "message": "Screen will stay on." if mode == "alwaysOn" else "Screen will sleep after 3 minutes of inactivity.",
    }

    if mode == "sleep3" and not _display_power_commands("off"):
        response["warning"] = "Screen sleep was saved, but no display power command was found on this system."

    idle_config = _configure_display_idle(mode)
    if idle_config.get("attempts"):
        response["idleConfigured"] = bool(idle_config.get("ok"))

    _note_display_activity(wake=True)

    if mode == "alwaysOn":
        power = _set_display_power("on")
        if not power.get("ok"):
            response["warning"] = power.get("message", "Display power command was unavailable.")
        else:
            response["command"] = power.get("command")
    return response


def _read_display_mode() -> str:
    try:
        payload = json.loads(DISPLAY_STATE_FILE.read_text(encoding="utf-8"))
        mode = str(payload.get("mode", "alwaysOn"))
        return mode if mode in DISPLAY_MODES else "alwaysOn"
    except (OSError, json.JSONDecodeError):
        return "alwaysOn"


def _autostart_supported() -> bool:
    return os.name != "nt"


def _autostart_desktop_text() -> str:
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            "Name=NashTrack",
            "Comment=Launch NashTrack sports dashboard",
            f"Exec=python3 {ROOT_DIR / 'main.py'}",
            f"Path={ROOT_DIR}",
            "Terminal=false",
            "StartupNotify=false",
            "X-GNOME-Autostart-enabled=true",
            "",
        ]
    )


def _autostart_status() -> dict[str, object]:
    if not _autostart_supported():
        return {
            "ok": True,
            "supported": False,
            "enabled": False,
            "message": "Launch at startup is available on the Raspberry Pi desktop session.",
        }

    enabled = AUTOSTART_FILE.exists()
    return {
        "ok": True,
        "supported": True,
        "enabled": enabled,
        "path": str(AUTOSTART_FILE),
        "message": "NashTrack will launch at startup." if enabled else "NashTrack startup launch is off.",
    }


def _set_autostart(enabled: bool) -> dict[str, object]:
    if not _autostart_supported():
        return {
            "ok": False,
            "supported": False,
            "message": "Launch at startup is only supported from the Raspberry Pi desktop session.",
        }

    try:
        if enabled:
            AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
            AUTOSTART_FILE.write_text(_autostart_desktop_text(), encoding="utf-8")
            AUTOSTART_FILE.chmod(AUTOSTART_FILE.stat().st_mode | stat.S_IXUSR)
        elif AUTOSTART_FILE.exists():
            AUTOSTART_FILE.unlink()
    except OSError as error:
        return {"ok": False, "supported": True, "message": f"Startup setting failed: {error}"}

    return _autostart_status()


class _UpdaterHandler(BaseHTTPRequestHandler):
    server_version = "NashTrackUpdater/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def _read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}

        body = self.rfile.read(min(length, 65536))
        if not body:
            return {}

        return json.loads(body.decode("utf-8"))

    def do_GET(self) -> None:
        route = self.path.split("?", 1)[0]
        if route == "/health":
            self._send_json(200, {"ok": True, "service": "Nash Track updater"})
            return
        if route == "/display":
            self._send_json(200, _display_status())
            return
        if route == "/startup":
            self._send_json(200, _autostart_status())
            return
        if route == "/update/check":
            result = _run_git_update_check()
            self._send_json(200 if result.get("ok") else 409, result)
            return
        self._send_json(404, {"ok": False, "message": "Unknown updater route."})

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        try:
            if route == "/update":
                result = _run_git_update()
                self._send_json(200 if result.get("ok") else 409, result)
                return

            if route == "/display":
                payload = self._read_json_body()
                result = _save_display_mode(str(payload.get("mode", "")))
                self._send_json(200 if result.get("ok") else 400, result)
                return

            if route == "/display/power":
                payload = self._read_json_body()
                result = _set_display_power(str(payload.get("state", "")))
                self._send_json(200 if result.get("ok") else 501, result)
                return

            if route == "/display/activity":
                self._read_json_body()
                result = _note_display_activity(wake=True)
                self._send_json(200 if result.get("ok") else 501, {**_display_status(), **result})
                return

            if route == "/display/test-sleep":
                self._read_json_body()
                result = _test_display_sleep()
                self._send_json(200 if result.get("ok") else 501, result)
                return

            if route == "/startup":
                payload = self._read_json_body()
                result = _set_autostart(bool(payload.get("enabled")))
                self._send_json(200 if result.get("ok") else 501, result)
                return

            self._send_json(404, {"ok": False, "message": "Unknown updater route."})
        except Exception as error:
            self._send_json(500, {"ok": False, "message": str(error)})


def _start_updater_server() -> None:
    global _updater_server, _updater_thread
    _start_display_watchdog()
    if _updater_is_ready():
        return
    if _updater_server:
        return

    try:
        _updater_server = ThreadingHTTPServer(("127.0.0.1", UPDATER_PORT), _UpdaterHandler)
    except OSError as error:
        print(f"Nash Track updater unavailable on port {UPDATER_PORT}: {error}")
        return

    _updater_thread = threading.Thread(
        target=_updater_server.serve_forever,
        name="NashTrackUpdater",
        daemon=True,
    )
    _updater_thread.start()
    print(f"Nash Track updater running at http://127.0.0.1:{UPDATER_PORT}/")


def _start_vite() -> subprocess.Popen[bytes]:
    vite_bin = WEB_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite_bin.exists():
        raise RuntimeError(
            "Vite is not installed yet. Run the install command in web/README.md, "
            "then start main.py again."
        )

    node = _node_executable()
    env = os.environ.copy()
    if PORTABLE_NODE_DIR.exists():
        env["PATH"] = f"{PORTABLE_NODE_DIR}{os.pathsep}{env.get('PATH', '')}"

    stdout_path = WEB_DIR / "web-vite.out.log"
    stderr_path = WEB_DIR / "web-vite.err.log"
    command = [str(node), str(vite_bin), "--host", HOST, "--port", str(PORT), "--strictPort"]

    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        return subprocess.Popen(
            command,
            cwd=WEB_DIR,
            env=env,
            stdout=stdout,
            stderr=stderr,
            creationflags=_creation_flags(),
        )


def _browser_candidates() -> list[Path]:
    explicit_browser = os.environ.get("NASH_TRACK_BROWSER")
    if explicit_browser:
        return [Path(explicit_browser)]

    if os.name != "nt":
        candidates = [
            Path(path)
            for path in (
                shutil.which("chromium-browser"),
                shutil.which("chromium"),
                shutil.which("google-chrome"),
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/usr/bin/google-chrome",
            )
            if path
        ]
        return candidates

    candidates: list[Path] = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData"):
        base = os.environ.get(env_name)
        if not base:
            continue
        candidates.extend(
            [
                Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe",
            ]
        )
    return candidates


def _open_app_window(url: str = URL) -> None:
    for browser in _browser_candidates():
        if browser.exists():
            args = [
                str(browser),
                f"--app={url}",
                "--new-window",
                f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
                "--force-device-scale-factor=1",
            ]
            if os.name != "nt":
                args.append("--start-fullscreen")
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_creation_flags(),
            )
            return

    webbrowser.open(url)


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_web_app(open_window: bool = True, wait: bool = True) -> int:
    if not WEB_DIR.exists():
        raise RuntimeError(f"Web app folder was not found: {WEB_DIR}")

    _start_updater_server()

    if _server_is_ready():
        print(f"Nash Track web server is already running at {URL}")
        if open_window:
            _open_app_window()
        return 0

    process = _start_vite()
    try:
        _wait_for_server(process)
        print(f"Nash Track web server running at {URL}")
        if open_window:
            _open_app_window()

        if not wait:
            return 0

        print("Press Ctrl+C to stop the web server.")
        while process.poll() is None:
            time.sleep(0.5)
        return process.returncode or 0
    except KeyboardInterrupt:
        print("\nStopping Nash Track web server...")
        _stop_process(process)
        return 0
    except Exception:
        _stop_process(process)
        raise
