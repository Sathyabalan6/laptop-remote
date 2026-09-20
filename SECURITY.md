# Security Policy

## ⚠️ Important: This is a LAN-only tool

Laptop Remote is designed to be used **on a trusted local network** (home Wi-Fi,
a phone hotspot, etc.). It is **not** intended to be exposed to the public
internet.

By default it:

- Serves plaintext HTTP (use `--ssl` for HTTPS/WSS).
- Uses the Werkzeug development server (`allow_unsafe_werkzeug=True`), which is
  not a hardened production server.
- Allows permissive CORS (`cors_allowed_origins="*"`), relying on bearer tokens
  for authorization.

**Do not port-forward this server to the internet.** If you need remote access,
put it behind a VPN (WireGuard/Tailscale) instead.

## Security model

- A random 6-digit **pairing PIN** is required to obtain a session token.
- PIN entry is **rate-limited** per IP address with escalating lockouts.
- The PIN **rotates** after each successful pairing and on revoke.
- All control endpoints require a **bearer token**.
- Companion/QR endpoints are restricted to **localhost**.

## Reporting a vulnerability

If you discover a security issue, please **do not open a public issue**.

Instead, report it privately via GitHub's
[Security Advisories](https://github.com/Sathyabalan6/laptop-remote/security/advisories/new)
("Report a vulnerability"), or contact the maintainer directly.

Please include:

- A description of the issue and its impact
- Steps to reproduce
- The version/commit affected

We will acknowledge your report as soon as possible and work with you on a fix
and coordinated disclosure.

## Supported versions

The latest release on the `main` branch is supported with security fixes.
