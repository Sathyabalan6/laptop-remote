#!/usr/bin/env python3
"""
Laptop Remote - Terminal / CLI Edition
======================================
Runs the Laptop Remote server purely inside the terminal / command prompt.
No Tkinter GUI desktop companion window is launched.

Usage:
  LaptopRemote-CLI.exe
  LaptopRemote-CLI.exe --pin 123456
  LaptopRemote-CLI.exe --pin=MyPin
"""
import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Laptop Remote - Terminal Edition')
    parser.add_argument('--pin', default=None, help='Set a custom pairing PIN/password')
    args, _ = parser.parse_known_args()

    from server import main
    try:
        main(no_gui=True, custom_pin=args.pin)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user (Ctrl+C). Goodbye!\n")
        sys.exit(0)
