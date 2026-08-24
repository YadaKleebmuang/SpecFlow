#!/usr/bin/env python3
"""
SpecFlow Unified Process Supervisor & LINE Development Runtime Launcher
========================================================================
Starts and orchestrates:
  1. Rasa Action Server (Port 5055)
  2. Rasa Core/NLU Server (Port 5005) with Final Authoritative Model
  3. Cloudflare Quick Tunnel (Public HTTPS Tunneling)
  4. Automatic LINE Messaging API Webhook Endpoint Update & Verification

Usage:
  .venv-rasa-deploy/bin/python run.py
"""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

# Ensure UTF-8 console encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ----------------------------------------------------------------------
# Constants & Path Resolution (Independent of CWD)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv-rasa-deploy"
VENV_PYTHON = VENV_DIR / "bin" / "python"
VENV_RASA = VENV_DIR / "bin" / "rasa"

FINAL_MODEL = (
    PROJECT_ROOT
    / "final_models"
    / "run-20260825-001846"
    / "20260825-001851-woolen-billet.tar.gz"
)
ENDPOINTS_FILE = PROJECT_ROOT / "app" / "rasa" / "endpoints.yml"
CREDENTIALS_FILE = PROJECT_ROOT / "app" / "rasa" / "credentials.yml"
ACTIONS_FILE = PROJECT_ROOT / "app" / "rasa" / "actions" / "actions.py"
ENV_FILE = PROJECT_ROOT / ".env"

ACTION_PORT = 5055
RASA_PORT = 5005

# ----------------------------------------------------------------------
# Process Supervisor Tracker
# ----------------------------------------------------------------------
class ManagedProcess:
    def __init__(self, name: str, proc: subprocess.Popen, port: Optional[int] = None):
        self.name = name
        self.proc = proc
        self.port = port

managed_processes: List[ManagedProcess] = []
shutdown_lock = threading.Lock()
is_shutting_down = False


def log_streamer(proc: subprocess.Popen, prefix: str):
    """Streams stdout/stderr lines from child process with formatted prefix."""
    try:
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                line_str = line.rstrip()
                if line_str:
                    # Filter out unnecessary heartbeats or secret-like tokens
                    print(f"[{prefix}] {line_str}", flush=True)
    except Exception:
        pass


def terminate_all_processes():
    """Gracefully terminates all child processes in reverse order."""
    global is_shutting_down
    with shutdown_lock:
        if is_shutting_down:
            return
        is_shutting_down = True

    print("\n" + "=" * 60, flush=True)
    print("🛑 Shutting down SpecFlow runtime processes...", flush=True)
    print("=" * 60, flush=True)

    # Order: 1. Tunnel -> 2. Rasa Server -> 3. Action Server
    for mp in reversed(managed_processes):
        if mp.proc.poll() is None:
            print(f"  • Stopping {mp.name} (PID {mp.proc.pid})...", flush=True)
            try:
                mp.proc.terminate()
                mp.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"    Force killing {mp.name} (PID {mp.proc.pid})...", flush=True)
                try:
                    mp.proc.kill()
                    mp.proc.wait(timeout=2)
                except Exception:
                    pass
            except Exception as e:
                print(f"    Error stopping {mp.name}: {e}", flush=True)

    print("✅ All SpecFlow child processes stopped. Ports released.", flush=True)


def signal_handler(sig, frame):
    terminate_all_processes()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ----------------------------------------------------------------------
# Helper Utilities
# ----------------------------------------------------------------------
def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def get_pid_on_port(port: int) -> Optional[str]:
    """Tries to find the PID listening on a port via lsof (macOS/Linux)."""
    try:
        res = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in res.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2:
                return f"PID {parts[1]} ({parts[0]})"
    except Exception:
        pass
    return None


def load_env_file(env_path: Path):
    """Loads KEY=VALUE from .env if present without overriding existing shell env."""
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                # Shell env takes precedence
                if key and key not in os.environ:
                    os.environ[key] = val


def find_cloudflared() -> Optional[Path]:
    """Finds the cloudflared binary dynamically."""
    # 1. System PATH
    which_path = shutil.which("cloudflared")
    if which_path:
        return Path(which_path)

    # 2. User local bin
    local_bin = Path.home() / ".local" / "bin" / "cloudflared"
    if local_bin.exists() and os.access(local_bin, os.X_OK):
        return local_bin

    # 3. Homebrew / standard Unix paths
    for candidate in [
        Path("/opt/homebrew/bin/cloudflared"),
        Path("/usr/local/bin/cloudflared"),
    ]:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate

    return None


# ----------------------------------------------------------------------
# LINE Messaging API Management (PUT / GET / POST Test)
# ----------------------------------------------------------------------
def update_line_webhook(access_token: str, webhook_url: str) -> Tuple[bool, str, bool, str]:
    """
    Updates the LINE webhook endpoint via official LINE Messaging API.
    Returns: (update_success, update_msg, is_active, test_status)
    """
    api_url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "SpecFlow-Runtime/1.0",
    }
    payload = json.dumps({"endpoint": webhook_url}).encode("utf-8")

    # 1. PUT Webhook Endpoint
    req = urllib.request.Request(api_url, data=payload, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}", False, "NOT_RUN"
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        return False, f"HTTP {e.code} Error: {error_body or e.reason}", False, "NOT_RUN"
    except Exception as e:
        return False, f"Connection failed: {e}", False, "NOT_RUN"

    # 2. GET Webhook Endpoint Details
    is_active = False
    try:
        get_req = urllib.request.Request(api_url, headers=headers, method="GET")
        with urllib.request.urlopen(get_req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            is_active = bool(data.get("active", False))
    except Exception:
        pass

    # 3. POST Webhook Test (if active)
    test_status = "SKIPPED (Use Webhook is OFF)"
    if is_active:
        test_url = "https://api.line.me/v2/bot/channel/webhook/test"
        test_payload = json.dumps({"endpoint": webhook_url}).encode("utf-8")
        test_req = urllib.request.Request(test_url, data=test_payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(test_req, timeout=10) as resp:
                test_data = json.loads(resp.read().decode("utf-8"))
                if test_data.get("success"):
                    test_status = "PASS (HTTP 200 OK)"
                else:
                    detail = test_data.get("reason") or test_data.get("detail") or "Failed"
                    test_status = f"FAIL ({detail})"
        except Exception as e:
            test_status = f"WARN ({e})"

    return True, "Updated successfully", is_active, test_status


# ----------------------------------------------------------------------
# Main Supervisor Flow
# ----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("🤖 SpecFlow — Unified Local & Live LINE Runtime Launcher")
    print("=" * 60)

    # ------------------------------------------------------------------
    # STAGE 1 — PREFLIGHT VALIDATION
    # ------------------------------------------------------------------
    print("\n[1/8] PREFLIGHT VALIDATION")
    
    # 1.1 Virtual environment binaries
    if not VENV_PYTHON.exists() or not VENV_RASA.exists():
        print(f"❌ Deployment environment not found at: {VENV_DIR}")
        print("   Please ensure .venv-rasa-deploy is created with Python 3.9.6.")
        sys.exit(1)

    # 1.2 Final Model
    if not FINAL_MODEL.exists():
        print(f"❌ Final model archive not found at: {FINAL_MODEL}")
        sys.exit(1)

    # 1.3 Rasa configurations & Actions
    if not ENDPOINTS_FILE.exists() or not CREDENTIALS_FILE.exists():
        print(f"❌ Missing Rasa config files in {PROJECT_ROOT / 'app' / 'rasa'}")
        sys.exit(1)

    if not ACTIONS_FILE.exists():
        print(f"❌ Missing Actions module at: {ACTIONS_FILE}")
        sys.exit(1)

    # 1.4 Cloudflared binary
    cloudflared_bin = find_cloudflared()
    if not cloudflared_bin:
        print("❌ cloudflared executable not found!")
        print("   Please install cloudflared or place it in ~/.local/bin/cloudflared")
        sys.exit(1)
    print(f"  • cloudflared binary : {cloudflared_bin}")

    # 1.5 Load & Validate Credentials
    load_env_file(ENV_FILE)
    secret_val = os.environ.get("LINE_CHANNEL_SECRET", "").strip()
    token_val = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()

    secret_status = "SET" if secret_val else "MISSING"
    token_status = "SET" if token_val else "MISSING"

    print(f"  • LINE_CHANNEL_SECRET       : {secret_status}")
    print(f"  • LINE_CHANNEL_ACCESS_TOKEN : {token_status}")

    if not secret_val or not token_val:
        print("\n❌ LINE Credentials are missing!")
        print(f"   Please create '{ENV_FILE}' containing:")
        print("     LINE_CHANNEL_SECRET=<your_channel_secret>")
        print("     LINE_CHANNEL_ACCESS_TOKEN=<your_channel_access_token>")
        print("   Or export them in your terminal shell before running.")
        sys.exit(1)

    print("  • Preflight checks passed.")

    # ------------------------------------------------------------------
    # STAGE 2 — PORT SAFETY CHECK
    # ------------------------------------------------------------------
    print("\n[2/8] PORT SAFETY CHECK")
    port_conflict = False

    if is_port_in_use(ACTION_PORT):
        pid_info = get_pid_on_port(ACTION_PORT) or "unknown"
        print(f"❌ Port {ACTION_PORT} (Action Server) is already in use by {pid_info}!")
        port_conflict = True

    if is_port_in_use(RASA_PORT):
        pid_info = get_pid_on_port(RASA_PORT) or "unknown"
        print(f"❌ Port {RASA_PORT} (Rasa Server) is already in use by {pid_info}!")
        port_conflict = True

    if port_conflict:
        print("\n⚠️  Please terminate the conflicting process before starting:")
        print(f"   Example: lsof -i :{ACTION_PORT} OR lsof -i :{RASA_PORT}")
        sys.exit(1)

    print("  • Ports 5055 and 5005 are available.")

    # Base environment for child processes
    child_env = os.environ.copy()
    pythonpath = f"{PROJECT_ROOT / 'app' / 'rasa'}:{PROJECT_ROOT}"
    if "PYTHONPATH" in child_env:
        child_env["PYTHONPATH"] = f"{pythonpath}:{child_env['PYTHONPATH']}"
    else:
        child_env["PYTHONPATH"] = pythonpath

    # ------------------------------------------------------------------
    # STAGE 3 — START RASA ACTION SERVER
    # ------------------------------------------------------------------
    print("\n[3/8] STARTING ACTION SERVER (Port 5055)...")
    action_cmd = [
        str(VENV_RASA),
        "run",
        "actions",
        "--actions",
        "actions.actions",
        "--port",
        str(ACTION_PORT),
    ]

    action_proc = subprocess.Popen(
        action_cmd,
        cwd=str(PROJECT_ROOT),
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    managed_processes.append(ManagedProcess("Action Server", action_proc, ACTION_PORT))

    threading.Thread(
        target=log_streamer, args=(action_proc, "ACTION"), daemon=True
    ).start()

    # Wait until Action Server listens on 5055
    action_ready = False
    for _ in range(30):
        if action_proc.poll() is not None:
            break
        if is_port_in_use(ACTION_PORT):
            action_ready = True
            break
        time.sleep(0.5)

    if not action_ready:
        print("❌ Action Server failed to start on port 5055!")
        terminate_all_processes()
        sys.exit(1)

    print(f"  • Action Server running (PID {action_proc.pid}) on port {ACTION_PORT}.")

    # ------------------------------------------------------------------
    # STAGE 4 — START RASA SERVER
    # ------------------------------------------------------------------
    print("\n[4/8] STARTING RASA CORE/NLU SERVER (Port 5005)...")
    rasa_cmd = [
        str(VENV_RASA),
        "run",
        "-m",
        str(FINAL_MODEL),
        "--endpoints",
        str(ENDPOINTS_FILE),
        "--credentials",
        str(CREDENTIALS_FILE),
        "--port",
        str(RASA_PORT),
        "--enable-api",
        "--cors",
        "*",
    ]

    rasa_proc = subprocess.Popen(
        rasa_cmd,
        cwd=str(PROJECT_ROOT),
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    managed_processes.append(ManagedProcess("Rasa Server", rasa_proc, RASA_PORT))

    threading.Thread(
        target=log_streamer, args=(rasa_proc, "RASA"), daemon=True
    ).start()

    # Wait until Rasa Server passes health check
    print("  • Loading final model and warming up pipeline (up to 60s)...")
    rasa_ready = False
    local_health_url = f"http://127.0.0.1:{RASA_PORT}/webhooks/line/"

    for _ in range(120):  # 60 seconds
        if rasa_proc.poll() is not None:
            break
        try:
            with urllib.request.urlopen(local_health_url, timeout=1) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "ok":
                        rasa_ready = True
                        break
        except Exception:
            pass
        time.sleep(0.5)

    if not rasa_ready:
        print("❌ Rasa Server failed health check on http://127.0.0.1:5005/webhooks/line/!")
        terminate_all_processes()
        sys.exit(1)

    print(f"  • Rasa Server running (PID {rasa_proc.pid}) — Local Health: PASS")

    # ------------------------------------------------------------------
    # STAGE 5 — START CLOUDFLARE QUICK TUNNEL
    # ------------------------------------------------------------------
    print("\n[5/8] STARTING CLOUDFLARE QUICK TUNNEL...")
    tunnel_cmd = [
        str(cloudflared_bin),
        "tunnel",
        "--protocol",
        "http2",
        "--url",
        f"http://127.0.0.1:{RASA_PORT}",
    ]

    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    managed_processes.append(ManagedProcess("Cloudflare Tunnel", tunnel_proc))

    public_url: Optional[str] = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Thread-safe container to hold the URL once detected
    url_event = threading.Event()

    def tunnel_reader():
        nonlocal public_url
        try:
            if tunnel_proc.stdout:
                for line in iter(tunnel_proc.stdout.readline, ""):
                    if not line:
                        break
                    line_str = line.rstrip()
                    if line_str:
                        print(f"[TUNNEL] {line_str}", flush=True)
                        if not public_url:
                            match = url_pattern.search(line_str)
                            if match:
                                public_url = match.group(0)
                                url_event.set()
        except Exception:
            pass

    threading.Thread(target=tunnel_reader, daemon=True).start()

    # Wait for URL detection (up to 30s)
    if not url_event.wait(timeout=30) or not public_url:
        print("❌ Cloudflare Tunnel failed to provide a public URL!")
        terminate_all_processes()
        sys.exit(1)

    print(f"  • Public Tunnel established: {public_url}")

    # ------------------------------------------------------------------
    # STAGE 6 — PUBLIC HEALTH CHECK
    # ------------------------------------------------------------------
    print("\n[6/8] VERIFYING PUBLIC HTTPS HEALTH CHECK...")
    public_health_url = f"{public_url}/webhooks/line/"
    public_webhook_url = f"{public_url}/webhooks/line/webhook"

    print(f"  • Target public URL: {public_health_url}")
    print("  • Waiting 6s for Cloudflare Edge DNS and tunnel synchronization...")
    time.sleep(6.0)

    public_healthy = False
    for attempt in range(30):
        try:
            req = urllib.request.Request(
                public_health_url,
                headers={"User-Agent": "SpecFlow-HealthCheck/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "ok":
                        public_healthy = True
                        break
        except Exception as e:
            if (attempt + 1) % 5 == 0:
                print(f"    ... still propagating ({attempt + 1}/30)...", flush=True)
            time.sleep(1.5)

    if not public_healthy:
        print(f"❌ Public health check failed at {public_health_url}")
        terminate_all_processes()
        sys.exit(1)

    print(f"  • Public Health Check ({public_health_url}): PASS")

    # ------------------------------------------------------------------
    # STAGE 7 — AUTOMATIC LINE WEBHOOK UPDATE
    # ------------------------------------------------------------------
    print("\n[7/8] UPDATING LINE WEBHOOK ENDPOINT...")
    up_ok, up_msg, is_active, test_status = update_line_webhook(
        token_val, public_webhook_url
    )

    if up_ok:
        print(f"  • Webhook Endpoint Updated : PASS ({public_webhook_url})")
        print(f"  • Webhook Active Status   : {'YES' if is_active else 'NO (Action Required)'}")
        print(f"  • LINE Webhook Test Call   : {test_status}")
        if not is_active:
            print("  ⚠️  NOTE: 'Use webhook' is currently disabled on LINE Developers Console.")
            print("     Please toggle 'Use webhook' to ON in your LINE Channel Messaging API settings.")
    else:
        print(f"  ⚠️  Automatic Webhook Update: {up_msg}")
        print(f"     Please manually set Webhook URL to: {public_webhook_url}")

    # ------------------------------------------------------------------
    # STAGE 8 — DASHBOARD READY SCREEN
    # ------------------------------------------------------------------
    print("\n" + "=" * 62)
    print("🚀 SPECFLOW LIVE RUNTIME IS READY")
    print("=" * 62)
    print(f"  Environment       : .venv-rasa-deploy (Python {sys.version.split()[0]})")
    print(f"  Action Server     : RUNNING (PID {action_proc.pid}) on port {ACTION_PORT}")
    print(f"  Rasa Server       : RUNNING (PID {rasa_proc.pid}) on port {RASA_PORT}")
    print(f"  Cloudflare Tunnel : RUNNING (PID {tunnel_proc.pid})")
    print(f"  Local LINE Health : PASS (http://127.0.0.1:{RASA_PORT}/webhooks/line/)")
    print(f"  Public Health     : PASS ({public_health_url})")
    print(f"  LINE Webhook URL  : {public_webhook_url}")
    print(f"  LINE Webhook Sync : {'PASS' if up_ok else 'MANUAL_REQUIRED'}")
    print(f"  Webhook Active    : {'YES' if is_active else 'NO (Toggle ON in LINE Console)'}")
    print("-" * 62)
    print("📱 You can now test messaging SpecFlow on LINE!")
    print("👉 Press Ctrl+C at any time to gracefully stop all services.")
    print("=" * 62 + "\n", flush=True)

    # ------------------------------------------------------------------
    # SUPERVISOR MONITORING LOOP
    # ------------------------------------------------------------------
    try:
        while True:
            for mp in managed_processes:
                ret = mp.proc.poll()
                if ret is not None:
                    print(f"\n⚠️  Process '{mp.name}' (PID {mp.proc.pid}) exited unexpectedly with code {ret}!")
                    terminate_all_processes()
                    sys.exit(ret if ret != 0 else 1)
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        terminate_all_processes()


if __name__ == "__main__":
    main()
