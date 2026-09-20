#!/usr/bin/env python3
"""Laptop Remote — Terminal / CLI entry point.

Runs the Laptop Remote server purely inside the terminal.

Usage:
    python -m laptop_remote [--pin 123456] [--port 5000] [--ssl] [--tray]
"""

import sys
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="laptop-remote", description="Laptop Remote - Terminal Edition")
    parser.add_argument("--pin", default=None, help="Set a custom pairing PIN/password")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind (default: 5000)")
    parser.add_argument("--ssl", action="store_true", help="Enable HTTPS/TLS encryption (auto-generates self-signed cert if none provided)")
    parser.add_argument("--ssl-cert", default=None, help="Path to SSL certificate (.pem/.crt)")
    parser.add_argument("--ssl-key", default=None, help="Path to SSL private key (.pem/.key)")
    parser.add_argument("--tray", action="store_true", help="Enable background system tray icon mode")
    return parser


def main(argv=None) -> int:
    args, _ = build_parser().parse_known_args(argv)

    from .server import main as run_server

    try:
        run_server(
            custom_pin=args.pin,
            ssl_enabled=args.ssl,
            ssl_cert=args.ssl_cert,
            ssl_key=args.ssl_key,
            port=args.port,
            tray_enabled=args.tray,
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user (Ctrl+C). Goodbye!\n")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
