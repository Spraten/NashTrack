from __future__ import annotations

import os
import json
import shutil
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
_updater_server: ThreadingHTTPServer | None = None
_updater_thread: threading.Thread | None = None


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


def _display_power_commands(state: str) -> list[list[str]]:
    value = "1" if state == "on" else "0"
    commands: list[list[str]] = []

    vcgencmd = shutil.which("vcgencmd")
    if vcgencmd:
        commands.append([vcgencmd, "display_power", value])

    xset = shutil.which("xset")
    if xset and os.environ.get("DISPLAY"):
        commands.append([xset, "dpms", "force", state])

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


def _set_display_power(state: str) -> dict[str, object]:
    if state not in DISPLAY_POWER_STATES:
        return {"ok": False, "message": f"Unknown display power state: {state}"}

    attempts: list[dict[str, object]] = []
    for command in _display_power_commands(state):
        result = _run_display_command(command)
        attempts.append(result)
        if result.get("ok"):
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
            self._send_json(200, {"ok": True, "mode": _read_display_mode()})
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

            self._send_json(404, {"ok": False, "message": "Unknown updater route."})
        except Exception as error:
            self._send_json(500, {"ok": False, "message": str(error)})


def _start_updater_server() -> None:
    global _updater_server, _updater_thread
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
