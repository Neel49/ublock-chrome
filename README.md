# ublock-chrome

**One-command installer for [uBlock Origin](https://github.com/gorhill/uBlock) on Google Chrome (macOS).**

Chrome is phasing out Manifest V2 extensions, which breaks uBlock Origin (the best ad blocker). This tool works around that by:

1. Downloading the latest uBlock Origin Chromium build from GitHub
2. Creating a macOS `.app` launcher that starts Chrome with MV2 compatibility flags
3. Auto-loading uBlock Origin via `--load-extension` so you don't have to manually install it

## Install (one command, then restart Chrome)

### Option A: Homebrew (recommended, no Python needed)

```bash
brew install Neel49/ublock-chrome/ublock-chrome
```

That's it. Brew downloads the tool, then automatically downloads uBlock Origin and creates the launcher app.

### Option B: pip

```bash
pip install ublock-chrome && ublock-chrome install
```

### Option C: curl (zero dependencies)

```bash
curl -sS https://raw.githubusercontent.com/Neel49/ublock-chrome/main/bin/ublock-chrome | bash
```

### Option D: From source

```bash
git clone https://github.com/Neel49/ublock-chrome.git && ublock-chrome/bin/ublock-chrome install
```

## Usage

### First-time setup

```bash
ublock-chrome install
```

This will:
- Download the latest uBlock Origin for Chromium
- Create a **Chrome (uBO)** app in `~/Applications/`
- Print next steps

Then:
1. **Quit Chrome** completely (Cmd + Q)
2. Open **Chrome (uBO)** from `~/Applications/` (or Spotlight)
3. Right-click the Dock icon → **Options → Keep in Dock**

### Update uBlock Origin

```bash
ublock-chrome update
```

### Relaunch Chrome with uBO

```bash
ublock-chrome launch
```

This quits any running Chrome instance and relaunches it with the correct flags + uBlock Origin loaded.

### Uninstall

```bash
ublock-chrome uninstall
pip uninstall ublock-chrome
```

## How it works

Chrome ignores Manifest V2 extensions by default in recent versions. This tool launches Chrome with:

```
--disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled
--load-extension=~/.ublock-chrome/extension/
```

The `--load-extension` flag tells Chrome to load the unpacked uBlock Origin extension directly from disk, so you never need to go through `chrome://extensions` or the Chrome Web Store.

The `--disable-features` flags re-enable Manifest V2 support so the extension actually works.

## Important notes

- **Always launch Chrome via the "Chrome (uBO)" app** (or `ublock-chrome launch`). If you open Chrome normally, the flags won't be active.
- **After Chrome updates**, Chrome may auto-relaunch without the flags. Just quit and reopen via the launcher.
- **macOS only** — this tool uses macOS-specific `.app` bundles and `open` commands.

## What gets installed where

| What | Where |
|------|-------|
| uBlock Origin extension | `~/.ublock-chrome/extension/` |
| Launcher .app | `~/Applications/Chrome (uBO).app` |
| Launcher .app (build) | `~/.ublock-chrome/Chrome (uBO).app` |

## License

MIT
