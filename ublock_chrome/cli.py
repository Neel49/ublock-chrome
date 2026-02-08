#!/usr/bin/env python3
"""
ublock-chrome CLI

One-command installer for uBlock Origin on Chrome (macOS).

What it does:
  1. Downloads the latest uBlock Origin Chromium build from GitHub releases
  2. Extracts it to ~/.ublock-chrome/extension/
  3. Creates a macOS .app launcher ("Chrome (uBO)") that starts Chrome with:
       --disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled
       --load-extension=<path-to-ublock>
  4. Installs the .app to ~/Applications/ so you can Dock-pin it

Usage:
  ublock-chrome install     # full install (default)
  ublock-chrome update      # re-download latest uBlock Origin
  ublock-chrome uninstall   # remove everything
  ublock-chrome launch      # quit Chrome & relaunch with uBO
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INSTALL_DIR = Path.home() / ".ublock-chrome"
EXTENSION_DIR = INSTALL_DIR / "extension"
APP_NAME = "Chrome (uBO).app"
GITHUB_API_LATEST = "https://api.github.com/repos/gorhill/uBlock/releases/latest"
CHROME_APP_PATH = "/Applications/Google Chrome.app"

MV2_FLAGS = (
    "--disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_header(text: str) -> None:
    width = 54
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)
    print()


def _print_step(n: int, text: str) -> None:
    print(f"  [{n}] {text}")


def _check_macos() -> None:
    if sys.platform != "darwin":
        print("Error: ublock-chrome is macOS-only.", file=sys.stderr)
        sys.exit(1)


def _check_chrome() -> None:
    if not Path(CHROME_APP_PATH).exists():
        print(
            f"Error: Google Chrome not found at {CHROME_APP_PATH}\n"
            "Install Chrome first, or set CHROME_APP_PATH if it's elsewhere.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def fetch_latest_release_url() -> tuple[str, str]:
    """Return (download_url, tag_name) for the latest Chromium build."""
    req = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={"User-Agent": "ublock-chrome-installer/1.0"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    tag = data.get("tag_name", "unknown")

    for asset in data.get("assets", []):
        name: str = asset["name"]
        if "chromium" in name.lower() and name.endswith(".zip"):
            return asset["browser_download_url"], tag

    raise RuntimeError(
        "Could not find a Chromium .zip asset in the latest uBlock Origin release.\n"
        f"Check https://github.com/gorhill/uBlock/releases/tag/{tag}"
    )


def download_and_extract(url: str) -> dict:
    """Download the zip from *url*, extract to EXTENSION_DIR, return manifest data."""
    # Clean previous install
    if EXTENSION_DIR.exists():
        shutil.rmtree(EXTENSION_DIR)
    EXTENSION_DIR.mkdir(parents=True, exist_ok=True)

    # Download
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        urllib.request.urlretrieve(url, tmp_path)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(EXTENSION_DIR)
    finally:
        os.unlink(tmp_path)

    # The zip often extracts into a single subdirectory (e.g. uBlock0.chromium/).
    # If so, move its contents up one level.
    children = list(EXTENSION_DIR.iterdir())
    if (
        len(children) == 1
        and children[0].is_dir()
        and (children[0] / "manifest.json").exists()
    ):
        subdir = children[0]
        for item in subdir.iterdir():
            shutil.move(str(item), str(EXTENSION_DIR / item.name))
        subdir.rmdir()

    manifest_path = EXTENSION_DIR / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"manifest.json not found after extraction in {EXTENSION_DIR}")

    with open(manifest_path) as f:
        return json.load(f)


def create_launcher_app() -> Path:
    """
    Build a macOS .app bundle that launches Chrome with MV2 flags
    and --load-extension pointing to the installed uBlock extension.

    Returns the path to the .app inside INSTALL_DIR.
    """
    app_dir = INSTALL_DIR / APP_NAME
    contents = app_dir / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"

    if app_dir.exists():
        shutil.rmtree(app_dir)
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    # ---- launcher shell script ----
    ext_path = str(EXTENSION_DIR)
    script = f"""#!/bin/bash
# ---------------------------------------------------------------
# Chrome (uBO) — auto-generated by ublock-chrome
# Launches Google Chrome with Manifest-V2 flags + uBlock Origin
# ---------------------------------------------------------------

CHROME_APP="{CHROME_APP_PATH}"

# If Chrome is already running, the flags will be ignored.
# Offer to quit & relaunch.
if pgrep -x "Google Chrome" > /dev/null 2>&1; then
    CHOICE=$(osascript -e '
        display dialog "Chrome is already running.\\n\\nFlags are only applied on a fresh launch. Quit Chrome and relaunch with uBlock Origin?" \\
            buttons {{"Cancel", "Quit Chrome & Relaunch"}} \\
            default button "Quit Chrome & Relaunch" \\
            with title "Chrome (uBO)" \\
            with icon caution' -e 'button returned of result' 2>/dev/null)

    if [ "$CHOICE" != "Quit Chrome & Relaunch" ]; then
        exit 0
    fi

    osascript -e 'tell application "Google Chrome" to quit' 2>/dev/null

    # Wait up to 15 s for Chrome to exit gracefully
    for i in $(seq 1 30); do
        pgrep -x "Google Chrome" > /dev/null 2>&1 || break
        sleep 0.5
    done

    # Force-kill stragglers
    if pgrep -x "Google Chrome" > /dev/null 2>&1; then
        pkill -9 -x "Google Chrome"
        sleep 1
    fi
fi

open -a "$CHROME_APP" --args \\
    {MV2_FLAGS} \\
    --load-extension="{ext_path}"
"""
    launcher = macos / "launch.sh"
    launcher.write_text(script)
    launcher.chmod(0o755)

    # ---- Info.plist ----
    plist = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>      <string>launch.sh</string>
    <key>CFBundleIdentifier</key>      <string>com.ublock-chrome.launcher</string>
    <key>CFBundleName</key>            <string>Chrome (uBO)</string>
    <key>CFBundleDisplayName</key>     <string>Chrome (uBO)</string>
    <key>CFBundleVersion</key>         <string>1.0</string>
    <key>CFBundlePackageType</key>     <string>APPL</string>
    <key>CFBundleIconFile</key>        <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>  <string>10.15</string>
    <key>NSHighResolutionCapable</key> <true/>
</dict>
</plist>
"""
    (contents / "Info.plist").write_text(plist)

    # ---- Icon (borrow Chrome's) ----
    chrome_icon = Path(CHROME_APP_PATH) / "Contents" / "Resources" / "app.icns"
    if chrome_icon.exists():
        shutil.copy2(chrome_icon, resources / "AppIcon.icns")

    return app_dir


def install_app_to_applications(app_dir: Path) -> Path:
    """Copy the .app into ~/Applications/ and return the destination path."""
    dest_dir = Path.home() / "Applications"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / APP_NAME

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(app_dir, dest)
    return dest


def quit_chrome_if_running() -> None:
    """Gracefully quit Chrome if it's running."""
    result = subprocess.run(
        ["pgrep", "-x", "Google Chrome"],
        capture_output=True,
    )
    if result.returncode != 0:
        return  # not running

    print("  Quitting Chrome...")
    subprocess.run(
        ["osascript", "-e", 'tell application "Google Chrome" to quit'],
        capture_output=True,
    )

    # Wait for exit
    import time

    for _ in range(30):
        r = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
        if r.returncode != 0:
            break
        time.sleep(0.5)
    else:
        subprocess.run(["pkill", "-9", "-x", "Google Chrome"], capture_output=True)
        time.sleep(1)

    print("  Chrome stopped.")


def launch_chrome_with_ubo() -> None:
    """Launch Chrome with MV2 flags + uBlock extension."""
    ext_path = str(EXTENSION_DIR)
    subprocess.Popen(
        [
            "open",
            "-a",
            CHROME_APP_PATH,
            "--args",
            MV2_FLAGS,
            f"--load-extension={ext_path}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_install(_args: argparse.Namespace) -> None:
    _check_macos()
    _check_chrome()

    _print_header("uBlock Origin → Chrome Installer (macOS)")

    # 1. Download
    _print_step(1, "Fetching latest uBlock Origin release from GitHub...")
    url, tag = fetch_latest_release_url()
    print(f"      Release: {tag}")

    _print_step(2, "Downloading & extracting extension...")
    manifest = download_and_extract(url)
    name = manifest.get("name", "uBlock Origin")
    version = manifest.get("version", "?")
    print(f"      {name} v{version}")
    print(f"      Installed to: {EXTENSION_DIR}")

    # 2. Launcher app
    _print_step(3, "Creating 'Chrome (uBO)' launcher app...")
    app_dir = create_launcher_app()
    dest = install_app_to_applications(app_dir)
    print(f"      App saved to: {dest}")

    # 3. Done
    print()
    print("  " + "-" * 50)
    print("  Done! Here's what to do next:")
    print("  " + "-" * 50)
    print()
    print("  1. Quit Chrome completely         (Cmd + Q)")
    print(f"  2. Open 'Chrome (uBO)' from:      ~/Applications/")
    print("     Or run:  ublock-chrome launch")
    print()
    print("  Tip: Right-click the Dock icon → Options → Keep in Dock")
    print()
    print("  The launcher automatically:")
    print("    • Enables Manifest V2 extensions")
    print("    • Loads uBlock Origin into Chrome")
    print()
    print("  Other commands:")
    print("    ublock-chrome update      Re-download latest uBlock Origin")
    print("    ublock-chrome uninstall   Remove everything")
    print("    ublock-chrome launch      Quit Chrome & relaunch with uBO")
    print()


def cmd_update(_args: argparse.Namespace) -> None:
    _check_macos()
    _check_chrome()

    _print_header("Updating uBlock Origin")

    _print_step(1, "Fetching latest release...")
    url, tag = fetch_latest_release_url()
    print(f"      Release: {tag}")

    _print_step(2, "Downloading & extracting...")
    manifest = download_and_extract(url)
    print(f"      {manifest.get('name', 'uBlock Origin')} v{manifest.get('version', '?')}")

    # Rebuild the launcher in case paths changed
    _print_step(3, "Rebuilding launcher app...")
    app_dir = create_launcher_app()
    dest = install_app_to_applications(app_dir)
    print(f"      {dest}")

    print()
    print("  Updated! Restart Chrome to pick up the new version:")
    print("    ublock-chrome launch")
    print()


def cmd_uninstall(_args: argparse.Namespace) -> None:
    _check_macos()
    _print_header("Uninstalling uBlock Origin Chrome")

    targets = [
        INSTALL_DIR,
        Path.home() / "Applications" / APP_NAME,
    ]

    for p in targets:
        if p.exists():
            shutil.rmtree(p)
            print(f"  Removed: {p}")
        else:
            print(f"  (not found: {p})")

    print()
    print("  Done. uBlock Origin and the launcher have been removed.")
    print()


def cmd_launch(_args: argparse.Namespace) -> None:
    _check_macos()
    _check_chrome()

    if not EXTENSION_DIR.exists() or not (EXTENSION_DIR / "manifest.json").exists():
        print(
            "Error: uBlock Origin is not installed yet.\n"
            "Run:  ublock-chrome install",
            file=sys.stderr,
        )
        sys.exit(1)

    print("  Restarting Chrome with uBlock Origin...")
    quit_chrome_if_running()
    launch_chrome_with_ubo()
    print("  Chrome launched with uBlock Origin enabled.")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ublock-chrome",
        description="One-command installer for uBlock Origin on Chrome (macOS)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Download uBlock Origin, create launcher app (default)")
    sub.add_parser("update", help="Re-download the latest uBlock Origin")
    sub.add_parser("uninstall", help="Remove uBlock Origin and the launcher app")
    sub.add_parser("launch", help="Quit Chrome and relaunch with uBlock Origin")

    args = parser.parse_args()

    commands = {
        "install": cmd_install,
        "update": cmd_update,
        "uninstall": cmd_uninstall,
        "launch": cmd_launch,
    }

    # Default to install if no subcommand given
    cmd = commands.get(args.command, cmd_install)
    cmd(args)


if __name__ == "__main__":
    main()
