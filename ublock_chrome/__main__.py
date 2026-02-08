"""Allow `python3 -m ublock_chrome` to run install directly."""

from ublock_chrome.cli import cmd_install
import argparse

cmd_install(argparse.Namespace())
